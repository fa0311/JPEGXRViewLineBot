from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    FileMessage,
    ImageSendMessage,
)


import glob
import zipfile
import cv2
import imagecodecs
import shutil
import numpy as np



app = Flask(__name__)

line_bot_api = LineBotApi(
    ""
)
handler = WebhookHandler("")


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=FileMessage)
def handle_file(event):
    message_id = event.message.id

    message_content = line_bot_api.get_message_content(message_id)
    extension = event.message.file_name.split(".")[-1]

    with open(f"image/{message_id}.{extension}", "wb") as f:
        f.write(message_content.content)

    if extension == "zip":
        shutil.rmtree('image/tmp')

        with zipfile.ZipFile(f"image/{message_id}.{extension}") as existing_zip:
            existing_zip.extractall('image/tmp')

        files = glob.glob('image/tmp/*')
        if files[0].split(".")[-1] == "jxr":
            with open(files[0], 'rb') as fh:
                jpegxr = fh.read()
            # jpegxrをnumpy配列に
            numpy_array = imagecodecs.jpegxr_decode(jpegxr)
            # [0,1]を[0,255]へ
            numpy_array = np.clip(numpy_array * 255, a_min = 0, a_max = 255).astype(np.uint8)
            # BGRAに
            numpy_array = numpy_array[:, :, [2, 1, 0, 3]]
            # jpegで保存
            cv2.imwrite(f'image/{message_id}.jpg', numpy_array)
            line_bot_api.reply_message(event.reply_token, ImageSendMessage(
                original_content_url=f'https://example.com/image/{message_id}.jpg',
                preview_image_url=f'https://example.com/image/{message_id}.jpg'
            ))

if __name__ == "__main__":
    app.run(threaded=True)
