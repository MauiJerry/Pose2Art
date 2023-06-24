// c++ tool using TensorFlow Lite + OpenCV to capture Pose,
// display locally and send via UDP/OSC (Open Sound Control)
// forked from Q-engineering "TensorFlow_Lite_Pose_RPi_64-bits"
//    https://github.com/Qengineering/TensorFlow_Lite_Pose_RPi_64-bits
//    under BSD 3-Clause license
// the distributed build Env uses Code::Blocks http://www.codeblocks.org/ *.cbp
// My changes are (mostly) related to adding the OSC messaging

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netinet/in.h>

#include <opencv2/opencv.hpp>
#include <opencv2/dnn.hpp>
#include <opencv2/highgui.hpp>
#include <iostream>
#include <opencv2/core/ocl.hpp>
#include "tensorflow/lite/builtin_op_data.h"
#include "tensorflow/lite/interpreter.h"
#include "tensorflow/lite/kernels/register.h"
#include "tensorflow/lite/string_util.h"
#include "tensorflow/lite/model.h"
#include <cmath>

#include <osc++.hpp>

/////////////////////////////////////////////////////

#define PORT 5005
#define MAXLINE 1024

int terminateProgram;
int sockfd;
// Creating socket file descriptor
struct sockaddr_in destinationIPaddr;
char udp_buffer[MAXLINE];

// CTRL + C -> Sent SIGINT signal to the process.
void SIGINT_handler (int signal)
{
	terminateProgram = -1;
	printf("\nPOSE2OSC > SIGINT detected resources. Finishing the process and freeing up allocated resources.");
    if ( close(sockfd) < 0 ) {
        perror("\n POSE2OSC #> Closing socket file descriptor.");
        exit(EXIT_FAILURE);
    }
}

void start_UDPClient( )
 {
    printf("setup udp socket\n");
    // send OSC data
    if ((sockfd = socket(AF_INET, SOCK_DGRAM,0)) < 0)
    {
        perror("\nPose2OSC failed to create socket");
        exit(EXIT_FAILURE);
    }
    memset(&destinationIPaddr, 0, sizeof(destinationIPaddr));

    // Filling server information
    destinationIPaddr.sin_family = AF_INET;
    destinationIPaddr.sin_port = htons(PORT);
    destinationIPaddr.sin_addr.s_addr = inet_addr("10.10.10.10") ; // pc is 192:168:1:10 INADDR_ANY;
 }


//////////////////////////////////////////////////////////////////
using namespace cv;
using namespace std;
using namespace tflite;
int model_width;
int model_height;
int model_channels;
int image_width;
int image_height;
float image_aspect;

std::unique_ptr<Interpreter> interpreter;

//-----------------------------------------------------------------------------------------------------------------------
const char* Labels[] {
 "NOSE",                    //0
 "LEFT_EYE",                //1
 "RIGHT_EYE",               //2
 "LEFT_EAR",                //3
 "RIGHT_EAR",               //4
 "LEFT_SHOULDER",           //5
 "RIGHT_SHOULDER",          //6
 "LEFT_ELBOW",              //7
 "RIGHT_ELBOW",             //8
 "LEFT_WRIST",              //9
 "RIGHT_WRIST",             //10
 "LEFT_HIP",                //11
 "RIGHT_HIP",               //12
 "LEFT_KNEE",               //13
 "RIGHT_KNEE",              //14
 "LEFT_ANKLE",              //15
 "RIGHT_ANKLE"              //16
};

int osc_msg_send(osc::message msg)
{
//int sockfd;
// Creating socket file descriptor
//struct sockaddr_in destinationIPaddr;
//char udp_buffer[MAXLINE];
  auto packet = msg.to_packet();

  //int inSize = strlen(udp_buffer);
  ssize_t ret = sendto(
    sockfd, packet.data(), packet.size(), 0,
    (const struct sockaddr*)(&destinationIPaddr),
    sizeof(destinationIPaddr));

  //printf("| sent %d \n", (int)ret);

  return ret;
}

void sendOSCFrameInfo() //int width, int height, int channels)
{
    cout << "Frame width " << image_width << " height "<< image_height;
    sprintf(udp_buffer,"/image-width");
        osc::message msgW = osc::message(udp_buffer);
        msgW << udp_buffer << image_width;
        osc_msg_send(msgW);

    sprintf(udp_buffer,"/image-height");
        osc::message msgH = osc::message(udp_buffer);
        msgH << udp_buffer << image_height;
        osc_msg_send(msgH);

    sprintf(udp_buffer,"/numLandmarks");
        osc::message msgC = osc::message(udp_buffer);
        msgC << udp_buffer << 17; //channels;
        osc_msg_send(msgC);
}

void sendOSCLandmarks(Point* locations, float *confidence)
{
    int i;
    // clear udp_buffer
    // for each point, send 3 messages "/landmark-#  Loc[i].x Loc[i].y Cnf[i]

    // really should do some check in case there are <17 values but bah
    // also would be good to support MultiPose here
    for(i=0;i< 17;i++)
    {
        // skip point if confidence is too low; just my guess on threshold
        if (confidence[i] < -1.0) continue;

        // munge the locations to floats to match TouchDesigner expectations
        float x = float(locations[i].x)/float(image_width);
        float y = float(locations[i].y)/float(image_height);
        y = (1-y)/image_aspect;

        printf("/location %d xyz: %d=%f %d=%f %f", i, locations[i].x,x,locations[i].y,y, confidence[i]);
        // an alternative OSC pose message set using bundle paths
        //sprintf(udp_buffer,"/pose/0/keypoints/%d/x %d", i, points[i].x);
        sprintf(udp_buffer,"/landmark-%d-x", i);
        osc::message msgx = osc::message(udp_buffer);
        msgx << udp_buffer << x;//locations[i].x;
        osc_msg_send(msgx);

        // send buffer
        //sprintf(udp_buffer,"/pose/0/keypoints/%d/y %d", i, points[i].y);
        //sprintf(udp_buffer,"/landmark-%d-y %d", i, locations[i].y);
        sprintf(udp_buffer,"/landmark-%d-y", i);
        osc::message msgy = osc::message(udp_buffer);
        msgy << udp_buffer << y;//locations[i].y;
        osc_msg_send(msgy);

        //sprintf(udp_buffer,"/pose/0/keypoints/%d/score %0.2f", i, confidence[i]);
        //sprintf(udp_buffer,"/landmark-%d-z %0.2f", i, confidence[i]);
        //udp_send();
        sprintf(udp_buffer,"/landmark-%d-z", i);
        osc::message msgz = osc::message(udp_buffer);
        msgz << udp_buffer << confidence[i];
        osc_msg_send(msgz);
    }

}

//-----------------------------------------------------------------------------------------------------------------------
void GetImageTFLite(float* out, Mat &src)
{
    int i,Len;
    float f;
    uint8_t *in;
    static Mat image;

    // copy image to input as input tensor
    cv::resize(src, image, Size(model_width,model_height),INTER_NEAREST);

    //model posenet_mobilenet_v1_100_257x257_multi_kpt_stripped.tflite runs from -1.0 ... +1.0
    //model multi_person_mobilenet_v1_075_float.tflite                 runs from  0.0 ... +1.0
    in=image.data;
    Len=image.rows*image.cols*image.channels();
    for(i=0;i<Len;i++){
        f     =in[i];
        out[i]=(f - 127.5f) / 127.5f;
    }
}

//-----------------------------------------------------------------------------------------------------------------------

// This is where the magic happens; a single frame is given, model run, shapes/pose returned
void detect_from_video(Mat &src)
{
    int i,x,y,j;
    static Point Pnt[17];                       //heatmap
    static float Cnf[17];                       //confidence table
    static Point Loc[17];                       //location in image
    const float confidence_threshold = -1.0;    //confidence can be negative

    // snag source image size
    image_width = src.cols;
    image_height = src.rows;
    image_aspect = float(image_height)/float(image_width);


    GetImageTFLite(interpreter->typed_tensor<float>(interpreter->inputs()[0]), src);

    interpreter->Invoke();      // run your model

    // 1 * 9 * 9 * 17 contains heatmaps
    const float* heatmapShape = interpreter->tensor(interpreter->outputs()[0])->data.f;
    // 1 * 9 * 9 * 34 contains offsets
    const float* offsetShape = interpreter->tensor(interpreter->outputs()[1])->data.f;
    // 1 * 9 * 9 * 32 contains forward displacements
//    const float* dispFwdShape = interpreter->tensor(interpreter->outputs()[2])->data.f;
    // 1 * 9 * 9 * 32 contains backward displacements
//    const float* dispBckShape = interpreter->tensor(interpreter->outputs()[3])->data.f;

    // Finds the (row, col) locations of where the keypoints are most likely to be.
    for(i=0;i<17;i++){
        Cnf[i]=heatmapShape[i];     //x=y=0 -> j=17*(9*0+0)+i; -> j=i
        for(y=0;y<9;y++){
            for(x=0;x<9;x++){
                j=17*(9*y+x)+i;
                if(heatmapShape[j]>Cnf[i]){
                    Cnf[i]=heatmapShape[j];
                    Pnt[i].x=x;
                    Pnt[i].y=y;
                }
            }
        }
    }

    // Calculating the x and y coordinates of the keypoints with offset adjustment.
    for(i=0;i<17;i++){
        x=Pnt[i].x; y=Pnt[i].y; j=34*(9*y+x)+i;
        Loc[i].y=(y*src.rows)/8 + offsetShape[j   ];
        Loc[i].x=(x*src.cols)/8 + offsetShape[j+17];
    }

    sendOSCFrameInfo();
    sendOSCLandmarks(Loc, Cnf);

    for(i=0;i<17;i++){
        if(Cnf[i]>confidence_threshold){
            circle(src,Loc[i],4,Scalar( 255, 255, 0 ),FILLED);
        }
    }
    if(Cnf[ 5]>confidence_threshold){
        if(Cnf[ 6]>confidence_threshold) line(src,Loc[ 5],Loc[ 6],Scalar( 255, 255, 0 ),2);
        if(Cnf[ 7]>confidence_threshold) line(src,Loc[ 5],Loc[ 7],Scalar( 255, 255, 0 ),2);
        if(Cnf[11]>confidence_threshold) line(src,Loc[ 5],Loc[11],Scalar( 255, 255, 0 ),2);
    }
    if(Cnf[ 6]>confidence_threshold){
        if(Cnf[ 8]>confidence_threshold) line(src,Loc[ 6],Loc[ 8],Scalar( 255, 255, 0 ),2);
        if(Cnf[12]>confidence_threshold) line(src,Loc[ 6],Loc[12],Scalar( 255, 255, 0 ),2);
    }
    if(Cnf[ 7]>confidence_threshold){
        if(Cnf[ 9]>confidence_threshold) line(src,Loc[ 7],Loc[ 9],Scalar( 255, 255, 0 ),2);
    }
    if(Cnf[ 8]>confidence_threshold){
        if(Cnf[10]>confidence_threshold) line(src,Loc[ 8],Loc[10],Scalar( 255, 255, 0 ),2);
    }
    if(Cnf[11]>confidence_threshold){
        if(Cnf[12]>confidence_threshold) line(src,Loc[11],Loc[12],Scalar( 255, 255, 0 ),2);
        if(Cnf[13]>confidence_threshold) line(src,Loc[11],Loc[13],Scalar( 255, 255, 0 ),2);
    }
    if(Cnf[13]>confidence_threshold){
        if(Cnf[15]>confidence_threshold) line(src,Loc[13],Loc[15],Scalar( 255, 255, 0 ),2);
    }
    if(Cnf[14]>confidence_threshold){
        if(Cnf[12]>confidence_threshold) line(src,Loc[14],Loc[12],Scalar( 255, 255, 0 ),2);
        if(Cnf[16]>confidence_threshold) line(src,Loc[14],Loc[16],Scalar( 255, 255, 0 ),2);
    }
    cout << "\n";
}

//-----------------------------------------------------------------------------------------------------------------------
int main(int argc,char ** argv)
{

    float f;
    float FPS[16];
    int i=0;
    int In;
    int Fcnt=0;
    Mat frame;
    chrono::steady_clock::time_point Tbegin, Tend;

    cout << "Starting Pose2 OSC" << endl;

    signal(SIGINT, SIGINT_handler);
    terminateProgram = false;

    // setup socket
    start_UDPClient( );

    // setup tensorFLow --------------

    for(i=0;i<16;i++) FPS[i]=0.0;

    // Load model
    std::unique_ptr<FlatBufferModel> model = FlatBufferModel::BuildFromFile("posenet_mobilenet_v1_100_257x257_multi_kpt_stripped.tflite");

    // Build the interpreter
    ops::builtin::BuiltinOpResolver resolver;
    InterpreterBuilder(*model.get(), resolver)(&interpreter);

    interpreter->AllocateTensors();
    interpreter->SetAllowFp16PrecisionForFp32(true);
    interpreter->SetNumThreads(4);      //quad core

    // Get input dimension from the input tensor metadata
    // Assuming one input only
    In = interpreter->inputs()[0];
    model_height   = interpreter->tensor(In)->dims->data[1];
    model_width    = interpreter->tensor(In)->dims->data[2];
    model_channels = interpreter->tensor(In)->dims->data[3];
    cout << "height   : "<< model_height << endl;
    cout << "width    : "<< model_width << endl;
    cout << "channels : "<< model_channels << endl;

    //VideoCapture cap("Dance.mp4");
    VideoCapture cap(0);
    if (!cap.isOpened()) {
        cerr << "ERROR: Unable to open the camera" << endl;
        return 0;
    }

    cout << "Start grabbing, press ESC on Live window to terminate" << endl;

    while(1){
        cap >> frame;
        if (frame.empty()) {
            cerr << "End of movie" << endl;
            break;
        }

        //frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE);
        // most of the magic happens in this function
        detect_from_video(frame);

        Tend = chrono::steady_clock::now();
        //calculate frame rate
        f = chrono::duration_cast <chrono::milliseconds> (Tend - Tbegin).count();

        Tbegin = chrono::steady_clock::now();

        FPS[((Fcnt++)&0x0F)]=1000.0/f;
        for(f=0.0, i=0;i<16;i++){ f+=FPS[i]; }
        putText(frame, format("FPS %0.2f",f/16),Point(10,20),FONT_HERSHEY_SIMPLEX,0.6, Scalar(0, 0, 255));

        //show output
        imshow("RPi 4 - 1.95 GHz - 2 Mb RAM", frame);

        char esc = waitKey(5);
        if(esc == 27) break;
    }

    cout << "Closing the camera" << endl;

    // When everything done, release the video capture and write object
    cap.release();

    destroyAllWindows();
    cout << "Bye!" << endl;

    return 0;
}
