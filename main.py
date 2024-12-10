# * ============== Python ===================
import time
import os
from dotenv import load_dotenv
import uvicorn

# * ============== fastAPI ===================
from fastapi import FastAPI, Request, HTTPException, Header, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# * ============ Line SDK ==================
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import ApiClient, Configuration, MessagingApi, MessagingApiBlob, ReplyMessageRequest, TextMessage, FlexMessage, Emoji, ImageMessage
from linebot.v3.messaging.models.show_loading_animation_request import ShowLoadingAnimationRequest
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent


# * =========== Setup Env ===================

load_dotenv()
get_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
get_channel_secret = os.getenv('LINE_CHANNEL_SECRET')
# * ====================================

# * ============ Fast-API SETUP ===================
app = FastAPI()
app.mount("/images", StaticFiles(directory="images"), name="images")

# * ============ Line Setup ===================
configuration = Configuration(access_token=get_access_token)
handler = WebhookHandler(channel_secret=get_channel_secret)
# * ====================================


# ? function ====================================
from predict import predict_image
# ? =============================================


# !  ============= API =======================

@app.post("/predict")
def upload_image(image: UploadFile = File(...)):
    """
    Object Detection from an image.

    Args:
        file (bytes): The image file in bytes format.
    Returns:
        dict: JSON format containing the Objects Detections.
    """
    try:

        return {"file":image.filename,"file_size":image.size, "message": "Upload successful"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Upload failed: {str(e)}"})





@app.post("/callback")
async def callback(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()
    body_str = body.decode('utf-8')
    try:
        handler.handle(body_str, x_line_signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        raise HTTPException(status_code=400, detail="Invalid signature.")

    return 'OK'

#!  ============= API ======================




# ? ============= LINE ==================
@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event: ImageMessageContent):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)  # This is for sending text messages
        line_bot_blob_api = MessagingApiBlob(api_client)  # This is for handling image files

        try:
            folder_path = "images"
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)  # Create folder if it doesn't exist

            # Check if the message is an image
            if isinstance(event.message, ImageMessageContent):
                file_type = "image"
                file_name = os.path.join(folder_path, f"{event.message.id}.jpg")  # Define the file name and path
            else:
                return  # Do not support other message types

            # Get file content from LINE server
            file_content = line_bot_blob_api.get_message_content(event.message.id)

            # Save the image to the folder
            with open(file_name, "wb") as f:
                saved = f.write(file_content)  # Write the file content as bytes

            # If the file was saved successfully
            if saved:
                if os.path.exists(file_name):
                    
                    line_bot_api.show_loading_animation(
                        ShowLoadingAnimationRequest(
                            chat_id=event.source.user_id,
                            loadingSeconds=5
                        )
                    )
                   

                    # ! ========= send image to prediction ==========
                  
                    predict_result = predict_image(file_name)
                    
                    # ! =============================================
                    print(file_name)
                    # profile = line_bot_api.get_profile(user_id=event.source.user_id)
                    
                    line_bot_api.reply_message(
                        reply_message_request=ReplyMessageRequest(
                            replyToken=event.reply_token,
                            messages=[
                                
                                TextMessage(text=f"เมนูของคุณคือ : {predict_result}"),
                                # ImageMessage(originalContentUrl=f"http://127.0.0.1:8000/images/{event.message.id}.jpg", previewImageUrl=f"http://127.0.0.1:8000/images/{event.message.id}.jpg"),
                                
                            ]
                        )
                    )
                    print("Send message successfully")
    
                else:
                    print(f"Error: The file {file_name} does not exist.")
            else:
                print(f"Failed to save {file_type}: {file_name}")

        except Exception as e:
            print("Error:", e)



@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        if (event.message.text):
            try:
                # ? Loading animation
                line_bot_api.show_loading_animation(
                    ShowLoadingAnimationRequest(
                        chat_id=event.source.user_id,
                        loadingSeconds=5
                    )
                )
                # Reply Message
                if (event.message.text == "เเก้ไขเมนู"):
                    line_bot_api.reply_message(
                        reply_message_request=ReplyMessageRequest(
                            replyToken=event.reply_token,
                            messages=[
                                TextMessage(text="โปรดป้อนชื่อเมนูที่ถูกต้องหนูหน่อยค่ะ!")
                            ]
                        )
                    )
                # elif 
                else:
                    line_bot_api.reply_message(
                        reply_message_request=ReplyMessageRequest(
                            replyToken=event.reply_token,
                            messages=[
                                TextMessage(text="สวัสดีค่า!"),
                                TextMessage(text="มีรูปภาพของอาหารที่ต้องการให้หนูช่วยคำนวนเเคลอรี่มั้ยคะ ? 🎈"),
                            ]
                        )
                    )
                
                
            except Exception as e:
                print(e)
                return HTTPException(status_code=400, detail=e)
  
           
# ? LINE ====================================



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
