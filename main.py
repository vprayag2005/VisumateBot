import google.generativeai as genai
import os
import requests
import platform
import time
import wave
from gtts import gTTS
from mutagen.mp3 import MP3
from PIL import Image
from apscheduler.schedulers.blocking import BlockingScheduler
from moviepy import VideoFileClip, CompositeVideoClip,CompositeAudioClip, vfx, ImageClip, concatenate_videoclips,concatenate_audioclips, AudioFileClip
from typing import Final
from telegram import Update
from telegram.ext import Application,CommandHandler,MessageHandler,filters,ContextTypes
from dotenv import load_dotenv
from keep_alive import keep_alive

keep_alive()
load_dotenv()

TOKEN:Final=os.getenv("API_KEY")
BOT_USERNAME=os.getenv("BOT_USERNAME")

user_list:list=[]

#telegram bot start commands
async def startcommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi, I'm VisumateBot! Share your topic, and I'll transform it into an amazing video for you.")

async def landscapevideocommand(update:Update,context:ContextTypes.DEFAULT_TYPE):
    try:
        if(len(user_list)<4):
            if platform.system() == "Windows":
                base_path = "C:/VIDEO_AI/"
            else:
                base_path = "/opt/render/project/src/"
            user_id=update.message.chat.id
            user_list.append(user_id)
            path_image = os.path.join(base_path,f'temp_images/{user_id}')
            path_voice =  os.path.join(base_path,f'temp_audios/{user_id}')
            path_video =  os.path.join(base_path,f'temp_videos/{user_id}')
            text_list:list=context.args
            if(len(text_list)!=0):
                text:str=""
                for i in text_list:
                    text+=f'{i} '
                await update.message.reply_text("Generating Script ....")
                script_video=script(text)
                await update.message.reply_text("Script Generated sucessfull")
                os.mkdir(path_image)
                os.mkdir(path_voice)
                os.mkdir(path_video)
                await update.message.reply_text("Finding images for your video .....")
                generate_image(path_image,script_video)
                await update.message.reply_text("Image founded Sucessfully")
                await update.message.reply_text("Generating voices for your video....")
                generate_voice(path_voice,script_video)
                await update.message.reply_text("Voice generated sucessfully")
                await update.message.reply_text("Combining all togther to make video..")
                generate_video(path_video,path_image,path_voice,len(script_video))
                await update.message.reply_video(f"{path_video}/video.mp4")
                for i in range (0,len(script_video)):
                    os.remove(f'{path_image}/img{i+1}.jpeg')
                    os.remove(f'{path_video}/video{i+1}.mp4')
                    os.remove(f'{path_voice}/voice{i+1}.mp3')
                os.remove(f"{path_video}/video.mp4")
                os.remove(f"{path_video}/output.mp4")
                os.remove(f"{path_voice}/outputaudio.mp3")
                os.rmdir(path_video)
                os.rmdir(path_voice)
                os.rmdir(path_image)
            else:
               await update.message.reply_text("To create a landscape video, send the command /landscapevideo followed by your topic sentence.")
        else:
            await update.message.reply_text("Server is busy please try after some times")

    except Exception as e:
        print(e)
        await update.message.reply_text(e)
# generates normal message responses
def handle_responses(text:str)->str:
    return 

#normal chat message handle
async def handle_message(update:Update,context:ContextTypes.DEFAULT_TYPE):
    message_type:str=update.message.chat.type
    text:str=update.message.text
    if message_type=='group':
        await update.message.reply_text("group not suported")
    else:
        respone:str=handle_responses(text)
        await update.message.reply_text(respone)

# script generater
def script(topic:str)->list:
    genai.configure(api_key="AIzaSyDrUoASA7udFdHO5RTf94paUbSgE4KR5o8")
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content(f'''Create a 4-minute YouTube video script structured as a scene-by-scene voiceover, with corresponding image suggestions for each scene. Focus on the topic: '{topic}' Present the script in a 2D array format as follows: [[scene1, voiceover1, image suggestion1], [scene2, voiceover2, image suggestion2], ...]. Provide only the 2D array in python.''')
    cleaned_text = response.text.replace("```python", "").replace("```", "").strip()
    video_script_array = eval(cleaned_text.split('=', 1)[1].strip())
    return video_script_array

# image generator
def generate_image(path:str,script:list):
    for i in range (0,len(script)):
        response=requests.get(f'https://api.unsplash.com/search/photos?client_id=qbIjvlC7jv7m9M_w6q4RkQdv8IJRpUAqKiXt2j1izPE&query={script[i][2]}&orientation=landscape')
        response=response.json()
        image_url=response["results"][0]["urls"]["full"]
        data = requests.get(image_url).content
        with open(f'{path}/img{i+1}.jpeg', 'wb') as f:
            f.write(data)
        #Open an image
        image = Image.open(f'{path}/img{i+1}.jpeg')

        #Resize to specific dimensions (e.g., 300x200 pixels)
        resized_image = image.resize((1920,1080))
        resized_image.save(f'{path}/img{i+1}.jpeg')
        
#generates voices
def generate_voice(path:str,script:list):
    for i in range(0,len(script)):
        # Text
        text = f'{script[i][1]}'
        tts = gTTS(text, lang='en')
        tts.save(f"{path}/voice{i+1}.mp3")
   
#generte video
def generate_video(path_video:str,path_image:str,path_voice:str,length:int):
    video_clips=[]
    audio_clips=[]
    for i in range(length):
        audio_file = MP3(f"{path_voice}/voice{i+1}.mp3")
        duration = audio_file.info.length
        myclip = ImageClip(f"{path_image}/img{i+1}.jpeg", duration=int(duration))
        myclip.write_videofile(f"{path_video}/video{i+1}.mp4", codec="libx264", fps=24)
        video_clips.append(VideoFileClip(f"{path_video}/video{i+1}.mp4"))
        audio_clips.append(AudioFileClip(f"{path_voice}/voice{i+1}.mp3"))
    final_clip_audio = concatenate_audioclips(audio_clips)
    final_clip_audio.write_audiofile(f"{path_voice}/outputaudio.mp3")
    final_clip_video = concatenate_videoclips(video_clips, method="compose", padding=-1)
    final_clip_video.write_videofile(f"{path_video}/output.mp4", codec="libx264", fps=24)
    videoclip = VideoFileClip(f"{path_video}/output.mp4")
    audioclip = AudioFileClip(f"{path_voice}/outputaudio.mp3")

    new_audioclip = CompositeAudioClip([audioclip])
    videoclip.audio = new_audioclip
    videoclip.write_videofile(f"{path_video}/video.mp4")
def limit_user():
    for i in user_list:
        user_list.remove(i)
#fetch errors
async def error(update:Update,context:ContextTypes.DEFAULT_TYPE):
    print(f'update {update} caused error {context.error}')

if __name__== '__main__':

    if platform.system() == "Windows":
        base_path = "C:/VIDEO_AI"
    else:
        base_path = "/opt/render/project/src"
    if not (os.path.exists(f"{base_path}/temp_audios")):
        os.mkdir(f"{base_path}/temp_audios")
    if not(os.path.exists(f"{base_path}/temp_images")):
        os.mkdir(f"{base_path}/temp_images")
    if not(os.path.exists(f"{base_path}/temp_videos")):
        os.mkdir(f"{base_path}/temp_videos")  

    app= Application.builder().token(TOKEN).build()

    #commands
    app.add_handler(CommandHandler('start',startcommand))
    app.add_handler(CommandHandler('landscapevideo',landscapevideocommand))
    
    app.add_handler(MessageHandler(filters.TEXT,handle_message))
    #error
    app.add_error_handler(error)
    app.run_polling(poll_interval=5)
    scheduler = BlockingScheduler()
    scheduler.add_job(limit_user, 'interval', hours=1)
    scheduler.start()
        
