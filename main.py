import asyncio
import itertools
import os
import platform
import threading
from time import sleep
from typing import Final

import google.generativeai as genai
import requests
from dotenv import load_dotenv
from gtts import gTTS
from mutagen.mp3 import MP3
from PIL import Image
from apscheduler.schedulers.background import BackgroundScheduler
from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    ImageClip,
    VideoFileClip,
    concatenate_audioclips,
    concatenate_videoclips,
)
from telegram import InputFile, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)


load_dotenv()

TOKEN:Final=os.getenv("TELEGRAM_API_KEY")
BOT_USERNAME:Final=os.getenv("BOT_USERNAME")
GEMINI_API_KEY:Final=os.getenv("GEMINI_API_KEY")
UNSPLASH_API_KEY:Final=os.getenv("UNSPLASH_API_KEY")

user_list:list=[]
text_list:list
landscapevideo=1
portraitvideo=1
video_generating:bool=True

def telegram_bot(app: Application):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(app.run_polling(poll_interval=5))

def reset_userlist():
    scheduler1 = BackgroundScheduler()
    scheduler1.add_job(id='Scheduled task', func=limit_user, trigger='interval', minutes=5)
    scheduler1.start()

#telegram bot start commands
async def startcommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi, I'm VisumateBot! Share your topic, and I'll transform it into an amazing video for you.")

async def landscapevideocommand(update:Update,context:ContextTypes.DEFAULT_TYPE):
    try:
        global video_generating
        global user_list
        global text_list
        if(len(user_list)<4 and video_generating and len(text_list)!=0):
            user_id=update.message.chat.id
            user_list.append(user_id)
            option=update.message.text
            time:str="5 minutes"
            video_generating=False
            if platform.system() == "Windows":
                base_path = "C:/VIDEO_AI/"
            else:
                base_path = "/home/Victoryverse/"
            path_image = os.path.join(base_path,f'landscapevideo/temp_images/{user_id}')
            path_voice =  os.path.join(base_path,f'landscapevideo/temp_audios/{user_id}')
            path_video =  os.path.join(base_path,f'landscapevideo/temp_videos/{user_id}')
            #removing any previous files left due to network issues or other failures
            remove_files(path_image,path_video,path_voice)
            if(option=="1"):
                option="Normal video"
            elif(option=="2"):
                option="YouTube video"
            else:
                await update.message.reply_text("Please choose the correct option. You selected an invalid option.")
                return await video_category_selection_landscape(update,context)
            text:str=""
            for i in text_list:
                text+=f'{i} '
            await update.message.reply_text("Generating a script for a captivating landscape video.")
            script_video=script(text,option,time)
            await update.message.reply_text("Script generated successfully.")
            os.mkdir(path_image)
            os.mkdir(path_voice)
            os.mkdir(path_video)
            await update.message.reply_text("Searching for the perfect images for your video.")
            generate_image(path_image,script_video,"landscape")
            await update.message.reply_text("Images found successfully.")
            await update.message.reply_text("Generating the voice-over for your video.")
            generate_voice(path_voice,script_video)
            await update.message.reply_text("Voice-over generated successfully.")
            await update.message.reply_text("Combining all elements to create your video.")
            threading.Thread(target=generate_video, args=(path_video, path_image, path_voice, len(script_video), update)).start()
            ConversationHandler.END
        else:
            if(len(text_list)==0):
                await update.message.reply_text("To create a landscape video, send the command /landscapevideo followed by your topic sentence.")
            else:
             await update.message.reply_text("Server is busy please try after some times")

    except Exception as e:
        print(e)
      
async def portraitvideocommand(update:Update,context:ContextTypes.DEFAULT_TYPE): 
    try:
        global video_generating
        global user_list
        global text_list
        if(len(user_list)<4 and video_generating and len(text_list)!=0):
            user_id=update.message.chat.id
            user_list.append(user_id)
            video_generating=False
            time:str="60 second"
            option=update.message.text
            if platform.system() == "Windows":
                base_path = "C:/VIDEO_AI/"
            else:
                base_path = "/home/Victoryverse/"
            path_image = os.path.join(base_path,f'portraitvideo/temp_images/{user_id}')
            path_voice =  os.path.join(base_path,f'portraitvideo/temp_audios/{user_id}')
            path_video =  os.path.join(base_path,f'portraitvideo/temp_videos/{user_id}')
            
            #Removing any previous files left due to network issues or other failures
            remove_files(path_image,path_video,path_voice)
            if(option=="1"):
                option="Normal video"
            elif(option=="2"):
                option="YouTube shorts"
            elif(option=="3"):
                option="Instagram reel"
            else:
                await update.message.reply_text("Please choose the correct option. You selected an invalid option.")
                return await video_category_selection_portrait(update,context)
            text:str=""
            for i in text_list:
                text+=f'{i} '
            await update.message.reply_text("Generating a script for a captivating portrait video.")
            script_video=script(text,option,time)
            await update.message.reply_text("Script generated successfully")
            os.mkdir(path_image)
            os.mkdir(path_voice)
            os.mkdir(path_video)
            await update.message.reply_text("Searching for the perfect images for your video.")
            generate_image(path_image,script_video,"portrait")
            await update.message.reply_text("Images found successfully.")
            await update.message.reply_text("Generating the voice-over for your video")
            generate_voice(path_voice,script_video)
            await update.message.reply_text("Voice-over generated successfully.")
            await update.message.reply_text("Combining all elements to create your video.")
            # Create and start the thread
            threading.Thread(target=generate_video, args=(path_video, path_image, path_voice, len(script_video), update)).start()
            ConversationHandler.END
        
        else:
            if(len(text_list)==0):
                await update.message.reply_text("To create a portrait video, send the command /portraitvideo followed by your topic sentence.")
            else:
                await update.message.reply_text("Server is busy please try after some times")

    except Exception as e:
        print(e)
        await update.message.reply_text(e)
async def video_category_selection_landscape(update:Update,context:ContextTypes.DEFAULT_TYPE):
    global text_list
    text_list=context.args
    await update.message.reply_text("Choose the platform by entering the corresponding number:")
    await update.message.reply_text("1. Normal Video\n2. YouTube Video\n")
    return landscapevideo

async def video_category_selection_portrait(update:Update,context:ContextTypes.DEFAULT_TYPE):
    global text_list
    text_list=context.args
    await update.message.reply_text("Choose the platform by entering the corresponding number:")
    await update.message.reply_text("1. Normal Video\n2. YouTube Video\n3. Instagram Video")
    return portraitvideo

#remove files
def remove_files(path_image:str,path_video:str,path_voice:str):
    if(os.path.exists(path_image) and os.path.exists(path_video) and os.path.exists(path_voice)):
        for image,video,audio in itertools.zip_longest(os.listdir(path_image),os.listdir(path_video),os.listdir(path_voice)):
            if image is not None:
                os.remove(os.path.join(path_image,image))
            if video is not None:
                os.remove(os.path.join(path_video,video))
            if audio is not None:
                os.remove(os.path.join(path_voice,audio))
    elif(os.path.exists(path_image) and os.path.exists(path_video)):
        for image,video in itertools.zip_longest(os.listdir(path_image),os.listdir(path_video)):
            if image is not None:
                os.remove(os.path.join(path_image,image))
            if video is not None:
                os.remove(os.path.join(path_video,video))
    elif(os.path.exists(path_video) and os.path.exists(path_voice)):
        for video,audio in itertools.zip_longest(os.listdir(path_video),os.listdir(path_voice)):
            if video is not None:
                os.remove(os.path.join(path_video,video))
            if audio is not None:
                os.remove(os.path.join(path_voice,audio))
    elif(os.path.exists(path_image) and os.path.exists(path_voice)): 
        for image,audio in itertools.zip_longest(os.listdir(path_image),os.listdir(path_voice)):
            if image is not None:
                os.remove(os.path.join(path_image,image))
            if audio is not None:
                os.remove(os.path.join(path_voice,audio))
    elif(os.path.exists(path_image)):
        for image in (os.listdir(path_image)):
            os.remove(os.path.join(path_image,image))
    elif(os.path.exists(path_image)):
        for video in (os.listdir(path_video)):
            os.remove(os.path.join(path_video,video))
    elif(os.path.exists(path_voice)):
        for voice in (os.listdir(path_voice)):
            os.remove(os.path.join(path_voice,voice))
    if(os.path.exists(f"{path_video}/video.mp4")):
        os.remove(f"{path_video}/video.mp4")
    if(os.path.exists(f"{path_video}/output.mp4")):
        os.remove(f"{path_video}/output.mp4")
    if(os.path.exists(f"{path_voice}/outputaudio.mp3")):
        os.remove(f"{path_voice}/outputaudio.mp3")
    if(os.path.exists(path_video)):
        os.rmdir(path_video)
    if(os.path.exists(path_voice)):
        os.rmdir(path_voice)
    if(os.path.exists(path_image)):
        os.rmdir(path_image)
        
# script generater
def script(topic:str,option:str,time:str)->list:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content(f'''Create a {time} {option} script structured as a scene-by-scene voiceover, with corresponding image suggestions for each scene. Focus on the topic: '{topic}' Present the script in a 2D array format as follows: [[scene1, voiceover1, image suggestion1], [scene2, voiceover2, image suggestion2], ...]. Provide only the 2D array in python.''')
    cleaned_text = response.text.replace("```python", "").replace("```", "").strip()
    video_script_array = eval(cleaned_text.split('=', 1)[1].strip())
    return video_script_array

# image generator
def generate_image(path:str,script:list,orientation:str):
    for i in range (0,len(script)):
        response=requests.get(f'https://api.unsplash.com/search/photos?client_id={UNSPLASH_API_KEY}&query={script[i][2]}&orientation={orientation}')
        if response.status_code == 200:
            response=response.json()
            image_url=response["results"][0]["urls"]["full"]
            data = requests.get(image_url).content
            with open(f'{path}/img{i+1}.jpeg', 'wb') as f:
                f.write(data)
            #Open an image
            image = Image.open(f'{path}/img{i+1}.jpeg')

            #Resize to specific dimensions 
            if orientation == "portrait":
                resized_image = image.resize((1080,1920))
            else:
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
def generate_video(path_video:str,path_image:str,path_voice:str,length:int,update:Update):
    video_clips=[]
    audio_clips=[]
    for i in range(length):
        audio_file = MP3(f"{path_voice}/voice{i+1}.mp3")
        duration = audio_file.info.length
        myclip = ImageClip(f"{path_image}/img{i+1}.jpeg", duration=int(duration))
        myclip.write_videofile(f"{path_video}/video{i+1}.mp4", codec="libx264", fps=24)
        video_clips.append(VideoFileClip(f"{path_video}/video{i+1}.mp4"))
        audio_clips.append(AudioFileClip(f"{path_voice}/voice{i+1}.mp3"))
        sleep(60)
    final_clip_audio = concatenate_audioclips(audio_clips)
    final_clip_audio.write_audiofile(f"{path_voice}/outputaudio.mp3")
    final_clip_video = concatenate_videoclips(video_clips, method="compose", padding=-1)
    final_clip_video.write_videofile(f"{path_video}/output.mp4", codec="libx264", fps=24)
    videoclip = VideoFileClip(f"{path_video}/output.mp4")
    audioclip = AudioFileClip(f"{path_voice}/outputaudio.mp3")
    new_audioclip = CompositeAudioClip([audioclip])
    videoclip.audio = new_audioclip
    videoclip.write_videofile(f"{path_video}/video.mp4")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)  
    loop.run_until_complete(video_sent(update, path_video, path_image, path_voice))

# sending video to user
async def video_sent(update:Update,path_video:str,path_image:str,path_voice:str):
    sleep(100)
    global video_generating
    with open(f"{path_video}/video.mp4", 'rb') as video_file:
        video = InputFile(video_file)
        await update.message.reply_video(video)
    remove_files(path_image,path_video,path_voice)
    await update.message.reply_text("Video generated successfully.")
    video_generating=True
    
#userlimit    
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
        base_path = "/home/Victoryverse"
    if not (os.path.exists(f"{base_path}/landscapevideo")):
        os.mkdir(f"{base_path}/landscapevideo")
    if not (os.path.exists(f"{base_path}/portraitvideo")):
        os.mkdir(f"{base_path}/portraitvideo")
        
    if (os.path.exists(f"{base_path}/landscapevideo") and not(os.path.exists(f"{base_path}/landscapevideo/temp_audios"))):
        os.mkdir(f"{base_path}/landscapevideo/temp_audios")
    if (os.path.exists(f"{base_path}/landscapevideo") and not(os.path.exists(f"{base_path}/landscapevideo/temp_videos"))):
        os.mkdir(f"{base_path}/landscapevideo/temp_videos")
    if (os.path.exists(f"{base_path}/landscapevideo") and not(os.path.exists(f"{base_path}/landscapevideo/temp_images"))):
        os.mkdir(f"{base_path}/landscapevideo/temp_images")

    if (os.path.exists(f"{base_path}/portraitvideo") and not(os.path.exists(f"{base_path}/portraitvideo/temp_audios"))):
        os.mkdir(f"{base_path}/portraitvideo/temp_audios")
    if (os.path.exists(f"{base_path}/portraitvideo") and not(os.path.exists(f"{base_path}/portraitvideo/temp_videos"))):
        os.mkdir(f"{base_path}/portraitvideo/temp_videos")
    if (os.path.exists(f"{base_path}/portraitvideo") and not(os.path.exists(f"{base_path}/portraitvideo/temp_images"))):
        os.mkdir(f"{base_path}/portraitvideo/temp_images")
    app= Application.builder().token(TOKEN).read_timeout(3600).build()

    #commands
    app.add_handler(CommandHandler('start',startcommand))
    conv_handler_landscape = ConversationHandler(
        entry_points=[CommandHandler("landscapevideo", video_category_selection_landscape)],
        states={
            landscapevideo: [(MessageHandler(filters.TEXT & ~filters.COMMAND, landscapevideocommand))],

        },
        fallbacks=[CommandHandler("landscapevideo", video_category_selection_landscape)], 
    )

    conv_handler_portrait = ConversationHandler(
        entry_points=[CommandHandler("portraitvideo", video_category_selection_portrait)],
        states={
            portraitvideo: [(MessageHandler(filters.TEXT & ~filters.COMMAND, portraitvideocommand))],

        },
        fallbacks=[CommandHandler("portraitvideo", video_category_selection_portrait)], 
    )
    app.add_handler(conv_handler_portrait)
    app.add_handler(conv_handler_landscape)
    #error
    app.add_error_handler(error)
    telegram_thread = threading.Thread(target=telegram_bot, args=(app,))
    telegram_thread.start()

    reset_thread = threading.Thread(target=reset_userlist)
    reset_thread.start()
    
    # Keep the main thread alive
    while True:
        sleep(60)