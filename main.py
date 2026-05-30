import asyncio
import itertools
import os
import platform
import threading
from typing import Final
import json
import logging

import google.generativeai as genai
import requests
from dotenv import load_dotenv
from gtts import gTTS
from mutagen.mp3 import MP3
from PIL import Image
from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    ImageClip,
    VideoFileClip,
    concatenate_audioclips,
    concatenate_videoclips,
)
from moviepy.video.fx import CrossFadeIn
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TOKEN:Final=os.getenv("TELEGRAM_API_KEY")
BOT_USERNAME:Final=os.getenv("BOT_USERNAME")
GEMINI_API_KEY:Final=os.getenv("GEMINI_API_KEY")

user_list:list=[]
text_list:list
landscapevideo=1
portraitvideo=1
video_generating:bool=True



#telegram bot start commands
async def startcommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi, I'm VisumateBot! Share your topic, and I'll transform it into an amazing video for you.")

async def landscapevideocommand(update:Update,context:ContextTypes.DEFAULT_TYPE):
    try:
        global video_generating
        global user_list
        global text_list
        user_id=update.message.chat.id
        if(len(user_list)<4 and video_generating and len(text_list)!=0):
            user_list.append(user_id)
            option=update.message.text
            video_generating=False
            try:
                base_path = os.path.join(os.getcwd(), "temp_data")
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
                    video_generating=True
                    if user_id in user_list: user_list.remove(user_id)
                    return await video_category_selection_landscape(update,context)
                time = "5 minutes" # default
                topic_words = text_list
                
                if len(text_list) >= 2 and text_list[0].isdigit() and text_list[1].lower() in ["minute", "minutes", "second", "seconds", "min", "mins", "sec", "secs"]:
                    time = f"{text_list[0]} {text_list[1]}"
                    topic_words = text_list[2:]
                    
                text:str=" ".join(topic_words)
                await update.message.reply_text("Generating a script for a captivating landscape video.")
                script_video=script(text,option,time)
                await update.message.reply_text("Script generated successfully.")
                os.makedirs(path_image, exist_ok=True)
                os.makedirs(path_voice, exist_ok=True)
                os.makedirs(path_video, exist_ok=True)
                await update.message.reply_text("Searching for the perfect images for your video.")
                generate_image(path_image,script_video,"landscape")
                await update.message.reply_text("Images found successfully.")
                await update.message.reply_text("Generating the voice-over for your video.")
                generate_voice(path_voice,script_video)
                await update.message.reply_text("Voice-over generated successfully.")
                await update.message.reply_text("Combining all elements to create your video.")
                threading.Thread(target=generate_video, args=(path_video, path_image, path_voice, len(script_video), update, user_id)).start()
                ConversationHandler.END
            except Exception as e:
                video_generating=True
                if user_id in user_list: user_list.remove(user_id)
                raise e
        else:
            if(len(text_list)==0):
                await update.message.reply_text("To create a landscape video, send the command /landscapevideo followed by your topic sentence.")
            else:
             await update.message.reply_text("Server is busy please try after some times")

    except Exception as e:
        logger.error(f"Error in landscapevideocommand: {e}")
        await update.message.reply_text("An unexpected error occurred while processing your request.")
      
async def portraitvideocommand(update:Update,context:ContextTypes.DEFAULT_TYPE): 
    try:
        global video_generating
        global user_list
        global text_list
        user_id=update.message.chat.id
        if(len(user_list)<4 and video_generating and len(text_list)!=0):
            user_list.append(user_id)
            video_generating=False
            option=update.message.text
            try:
                base_path = os.path.join(os.getcwd(), "temp_data")
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
                    video_generating=True
                    if user_id in user_list: user_list.remove(user_id)
                    return await video_category_selection_portrait(update,context)
                time = "60 seconds" # default
                topic_words = text_list
                
                if len(text_list) >= 2 and text_list[0].isdigit() and text_list[1].lower() in ["minute", "minutes", "second", "seconds", "min", "mins", "sec", "secs"]:
                    time = f"{text_list[0]} {text_list[1]}"
                    topic_words = text_list[2:]
                    
                text:str=" ".join(topic_words)
                await update.message.reply_text("Generating a script for a captivating portrait video.")
                script_video=script(text,option,time)
                await update.message.reply_text("Script generated successfully")
                os.makedirs(path_image, exist_ok=True)
                os.makedirs(path_voice, exist_ok=True)
                os.makedirs(path_video, exist_ok=True)
                await update.message.reply_text("Searching for the perfect images for your video.")
                generate_image(path_image,script_video,"portrait")
                await update.message.reply_text("Images found successfully.")
                await update.message.reply_text("Generating the voice-over for your video")
                generate_voice(path_voice,script_video)
                await update.message.reply_text("Voice-over generated successfully.")
                await update.message.reply_text("Combining all elements to create your video.")
                # Create and start the thread
                threading.Thread(target=generate_video, args=(path_video, path_image, path_voice, len(script_video), update, user_id)).start()
                ConversationHandler.END
            except Exception as e:
                video_generating=True
                if user_id in user_list: user_list.remove(user_id)
                raise e
        
        else:
            if(len(text_list)==0):
                await update.message.reply_text("To create a portrait video, send the command /portraitvideo followed by your topic sentence.")
            else:
                await update.message.reply_text("Server is busy please try after some times")

    except Exception as e:
        logger.error(f"Error in portraitvideocommand: {e}")
        await update.message.reply_text("An unexpected error occurred while processing your request.")
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
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    response = model.generate_content(f'''Create a {time} {option} script structured as a scene-by-scene voiceover, with corresponding image suggestions for each scene. Focus on the topic: '{topic}' Present the script strictly as a valid JSON 2D array format as follows: [["scene1", "voiceover1", "image suggestion1"], ["scene2", "voiceover2", "image suggestion2"]]. Provide only the JSON output without markdown formatting.''')
    cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
    video_script_array = json.loads(cleaned_text)
    return video_script_array

# image generator
def generate_image(path:str,script:list,orientation:str):
    headers = {
        'User-Agent': 'VisumateBot/1.0 (https://github.com/vprayag2005/VisumateBot)'
    }

    def get_wiki_image(search_term):
        url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"filetype:bitmap {search_term}",
            "gsrnamespace": "6",
            "gsrlimit": "1",
            "prop": "imageinfo",
            "iiprop": "url",
            "format": "json"
        }
        try:
            res = requests.get(url, params=params, headers=headers)
            if res.status_code == 200:
                data = res.json()
                pages = data.get("query", {}).get("pages", {})
                for _, page_info in pages.items():
                    if "imageinfo" in page_info:
                        return page_info["imageinfo"][0]["url"]
        except Exception as e:
            logger.error(f"Error fetching from Wikimedia: {e}")
        return None

    for i in range (0,len(script)):
        query = script[i][2] if len(script[i]) > 2 else "background"
        image_url = get_wiki_image(query)
                
        if not image_url:
            # Fallback query if the specific one fails
            image_url = get_wiki_image("background")

        if image_url:
            data = requests.get(image_url, headers=headers).content
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
        else:
            # Ultimate fallback if no images found at all (solid color)
            if orientation == "portrait":
                img = Image.new('RGB', (1080, 1920), color = 'black')
            else:
                img = Image.new('RGB', (1920, 1080), color = 'black')
            img.save(f'{path}/img{i+1}.jpeg')

#generates voices
def generate_voice(path:str,script:list):
    for i in range(0,len(script)):
        # Text
        text = f'{script[i][1]}'
        tts = gTTS(text, lang='en')
        tts.save(f"{path}/voice{i+1}.mp3")

#generte video
def generate_video(path_video:str,path_image:str,path_voice:str,length:int,update:Update,user_id:int):
    try:
        video_clips=[]
        audio_clips=[]
        for i in range(length):
            audio_file = MP3(f"{path_voice}/voice{i+1}.mp3")
            duration = audio_file.info.length
            # Add 1 second to duration for overlap transition (except the last clip)
            clip_duration = int(duration) + (1 if i < length - 1 else 0)
            myclip = ImageClip(f"{path_image}/img{i+1}.jpeg", duration=clip_duration)
            myclip.write_videofile(f"{path_video}/video{i+1}.mp4", codec="libx264", fps=24)
            
            vid_clip = VideoFileClip(f"{path_video}/video{i+1}.mp4")
            if i > 0:
                vid_clip = vid_clip.with_effects([CrossFadeIn(1)])
            video_clips.append(vid_clip)
            
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
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)  
        loop.run_until_complete(video_sent(update, path_video, path_image, path_voice))
    except Exception as e:
        logger.error(f"Error in generate_video: {e}")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(update.message.reply_text("An error occurred during video generation."))
    finally:
        global video_generating
        video_generating = True
        if user_id in user_list:
            user_list.remove(user_id)

# sending video to user
async def video_sent(update:Update,path_video:str,path_image:str,path_voice:str):
    with open(f"{path_video}/video.mp4", 'rb') as video_file:
        video = InputFile(video_file)
        await update.message.reply_video(video)
    remove_files(path_image,path_video,path_voice)
    await update.message.reply_text("Video generated successfully.")

#fetch errors
async def error(update:Update,context:ContextTypes.DEFAULT_TYPE):
    logger.error(f'update {update} caused error {context.error}')

if __name__== '__main__':

    base_path = os.path.join(os.getcwd(), "temp_data")
    os.makedirs(f"{base_path}/landscapevideo/temp_audios", exist_ok=True)
    os.makedirs(f"{base_path}/landscapevideo/temp_videos", exist_ok=True)
    os.makedirs(f"{base_path}/landscapevideo/temp_images", exist_ok=True)

    os.makedirs(f"{base_path}/portraitvideo/temp_audios", exist_ok=True)
    os.makedirs(f"{base_path}/portraitvideo/temp_videos", exist_ok=True)
    os.makedirs(f"{base_path}/portraitvideo/temp_images", exist_ok=True)
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
    
    # Start the bot
    app.run_polling(poll_interval=5)