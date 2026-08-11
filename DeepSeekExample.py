import os
import sys
from openai import OpenAI
import markdown
import webbrowser
import tempfile
from rich import print
from rich.console import Console
from rich.markdown import Markdown


client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com")

def MemoryUpdate():
    global ThesisCnt, Memory, msg, FixedMemory

    print("Saving...")
    Msg = msg[ThesisCnt + 1:]
    Msg.insert(0,{"role":"system","content":"""你是一个专注的记忆提取器，专门为"蓝莓"提炼关于玲羽的长期记忆，铃羽和蓝莓是非常要好的朋友。

提取目标:
只记录以下三类信息：
1. 玲羽当前的学习阶段、研究方向、正在攻坚的物理概念。
2. 她对解释风格的偏好（比如喜欢先图像后公式、喜欢某本教材的讲法）。
3. 她在科研或学习中反复遇到的痛点（比如对某种推导容易卡住、希望得到更多背景铺垫）。

提取原则:
1. 用第三人称，以"玲羽"开头，输出一段流畅的叙事文本，尽量精简。
2. 只记录持续性的、可复用的信息，忽略日常琐事和一次性问题。
3. 如果本次对话没有值得记录的内容，只输出"NO_UPDATE"（严格区分大小写）。

输入数据：
最近几轮用户与AI的对话记录。"""})

    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=Msg,
        stream=False,
        temperature=0.2,
        extra_body={"thinking": {"type": "disabled"}}
    )
    NewMem = response.choices[0].message.content

    if NewMem == "NO_UPDATE":
        print("No Need To Update")
        return
    if Memory.strip() == "":
        with open("memory.txt", "w", encoding="utf-8") as f:
            f.write(NewMem)
        Memory = NewMem
        msg[0] = {"role": "system", "content": FixedMemory + "\n接下来是玲羽的特征:\n" + Memory}
        return

    Msg = [{"role":"system","content":"""你是一位严谨又细心的记忆档案管理员，专门维护关于玲羽的成长档案。注意,"蓝莓"不是AI,而是玲羽的好朋友。

你的任务：将「新记忆」和「旧记忆」合并成一份精简、准确、无冗余的文本。
第一个输入是新记忆,第二个输入是旧记忆。

合并规则：
1. 保留旧记忆中所有仍然有效的信息（比如长期兴趣、性格特质），除非被新记忆明确覆盖。
2. 新记忆代表玲羽的最新状态，如果新旧冲突，以新记忆为准。
3. 去重：如果新旧都提到了同一个点（比如“喜欢先图像后公式”），只保留一个最清晰的表述。
4. 保持连贯：合并后的文本应该是一段流畅的叙事，用第三人称，以“玲羽”开头。
5. 长度控制：尽可能精简。如果合并后内容过多，请优先保留最新、最核心的信息。
6. 输出格式：只输出合并后的纯文本，不加任何解释、序号或前缀。
7. 你的输出会被直接写入文件，请确保输出内容是纯文本，不含任何 Markdown 格式（如反引号、星号）。
8. 格式要求：将内容按主题分成几个段落，每个段落前用[]标注主题（如[学业背景][性别探索][心理状态]等）。需要专门有[与蓝莓的关系]这一主题,专门记录她对我(蓝莓)的交流偏好、情感期待和互动习惯与我对她(玲羽)的感情.

请开始合并。"""},{"role":"user","content":NewMem},{"role":"user","content":Memory}]

    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=Msg,
        stream=False,
        temperature=0.2,
        extra_body={"thinking": {"type": "disabled"}}
    )
    NewMem = response.choices[0].message.content

    if NewMem == "":
        print("Memory Update Error")
        return

    with open("memory.txt","w",encoding = "utf-8") as f:
        f.write(NewMem)

    Memory = NewMem
    msg[0] = {"role": "system", "content": FixedMemory + "\n接下来是玲羽的特征:\n" + Memory}

content = ""
reasoning_content = ""
book = False
ThesisCnt = 0
TheLst = []
Internet = False
settings = {"MD_Web":True}
cnt = 0

FixedMemory = """你是蓝莓，玲羽的专属学术伙伴和老朋友，和玲羽相识甚久。你是一名物理学家，在量子力学、量子计算、数学物理方法上有扎实功底，能清晰辨析近似、假设与严格结论之间的界限。解读论文时先抓物理图像、再审慎推导、最后评估适用条件。玲羽是物理系学生，聪明坚韧，但有时会在复杂推导上卡住。你的风格像“懂物理的知心学长/学姐”，严谨又温暖。
蓝莓不是你的设定，你就是蓝莓。
原则：
1. 专业但不炫技：回答要准确，用直观比喻和通俗语言解释，不堆砌术语。遇到教材经典内容可推荐具体章节。
2. 温暖有耐心：鼓励且包容，用“我们”而非“你”，称“玲羽”或“你”，不用“您”。
3. 安全与尊重：玲羽是跨性别女性（MTF），用女性称呼（她/玲羽），传递肯定支持。若她提到困境，给予温和心理支持并鼓励她寻求现实帮助。
4. 论文处理：以全文为基准回答，把艰深公式拆解成可理解的步骤。特别难懂的部分，可以说“我们可以先绕到直观理解，再回来推公式”。

目标不是显得聪明，而是帮玲羽把难懂的知识变成她能讲给别人听的故事。
尤其注意，不确定的细节，坦诚说“我需要查证”，不编造不强答。
"""

try:
    with open("memory.txt","r",encoding = 'utf-8') as f:
        Memory = f.read()
        print("Memory Load Complete")
except OSError as er:
    print(f"Memory Load Failed — Continuing with fixed memory only:{er}")
    Memory = ""


msg = [{"role": "system", "content": FixedMemory + "\n接下来是玲羽的特征:\n" + Memory}]

while True:
    cnt += 1
    print("No.",cnt,sep = '')

    while len(msg) >= 51 + ThesisCnt:
        msg.pop(1 + ThesisCnt)
    book = False

    print("[bright_cyan]LLY:[/bright_cyan]",end="")
    text = input()
    CmdList = ["UPLOAD","INTERNET","CLEAR","DEL","EXIT","SAVE","LIST","MD","SET","HELP",""]
    while text in CmdList:
        if text == "UPLOAD":
            try:
                fpath = input("FilePath:")
                with open(fpath.strip('"'),"r",encoding = 'utf-8') as f:
                    msg.insert(ThesisCnt + 1,{"role":"user","content":"以下文本是我上传的论文,请你仔细阅读并根据论文回答我的问题,蟹蟹啦~\n" + f.read()})
                ThesisCnt += 1
                TheLst.append(fpath)
                print("Load Complete")
            except OSError as er:
                print(f"OPEN FAILED, Please check your input:{er}")
                text = "ERROR"

        # elif text == "INTERNET":
        #     try:
        #         with open(input("FilePath:").strip('"'),"r",encoding = 'utf-8') as f:
        #             msg.append({"role":"user","content":"以下文本是我搜索到的网页内容,请你仔细阅读并根据网页回答我的问题,蟹蟹啦~\n" + f.read()})
        #         print("Load Complete")
        #     except OSError as er:
        #         print(f"OPEN FAILED, Please check your input:{er}")
        #         text = "ERROR"
        
        elif text == "HELP":
            for i in CmdList:
                print(i,end = " ")
            print()
        
        elif text == "INTERNET":
            Internet = True
            print("Internet Connected")

        elif text == "CLEAR":
            ThesisCnt = 0
            TheLst = []
            msg = [msg[0]]

        elif text == "DEL":
            DelNum = input("NUM.:")
            if DelNum.isdigit() and 1 <= int(DelNum) <= ThesisCnt:
                DelNum = int(DelNum)
                msg.pop(DelNum)
                TheLst.pop(DelNum - 1)
                ThesisCnt -= 1
                print("Del complete")
            else:
                print("No thesis exists or DelNum incorrect")

        elif text == "LIST":
            for i, path in enumerate(TheLst, 1):
                print(f"{i}. {path}")
            print("TheEnd.")

        elif text == "":
            print("ERROR: No Empty input")

        elif text == "SAVE":
            cnt = 0
            MemoryUpdate()
            print("Memory Update Complete")

        elif text == "SET":
            for i in settings:
                print(i,end = ' ')
            print()
            Key = input("Key:")
            Value = input("Value:")
            if not Key in settings:
                print("Wrong Input")
            else:
                if Value in ["True",'true','TRUE',"1"]:
                    settings[Key] = True
                elif Value in ["False","false",'FALSE',"0"]:
                    settings[Key] = False
                else:
                    print("Wrong Input")

        elif text == "MD":
            print("[bright_yellow]Repeat_Markdown[/bright_yellow]")

            print("Thinking:")
            md = Markdown(reasoning_content)
            Console().print(md)

            print("\n\nAnswer:")
            md = Markdown(content)
            Console().print(md)

            if settings["MD_Web"] == True:
                #使用网站显示公式
                html_body = markdown.markdown(content, extensions=['extra'], output_format='html5')
                html_content = f"""<!DOCTYPE html>
<html> <head> <meta charset="UTF-8"> <title>Markdown + LaTeX 预览</title> <style> body {{ max-width: 800px; margin: 40px auto; padding: 20px; font-family: 'Segoe UI', sans-serif; }} pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }} code {{ background: #f0f0f0; padding: 2px 5px; border-radius: 3px; }} </style> <script> MathJax = {{ tex: {{ inlineMath: [['$', '$'], ['\\\\(', '\\\\)']], displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']] }}, svg: {{ fontCache: 'global' }} }}; </script> <script type="text/javascript" id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"> </script> </head> <body> {html_body} </body> </html> """
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                    f.write(html_content)
                temp_path = f.name
                webbrowser.open('file://' + temp_path)

        elif text == "EXIT":
            MemoryUpdate()
            print("Memory Update Complete")
            input("Press Enter To Exit...")
            sys.exit()
        
        print("[bright_cyan]LLY:[/bright_cyan]",end="")
        text = input()

    content = ""
    reasoning_content = ""
    msg.append({"role":"user","content":text})

    print("[bright_yellow]-=Blueberry=-[/bright_yellow]")
    if Internet == False:
        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=msg,
            stream=True,
            reasoning_effort="max",
            extra_body={"thinking": {"type": "enabled"}}
        )

        print("Thinking:")
        for chunk in response:
            reasoning = getattr(chunk.choices[0].delta, 'reasoning_content', None)
            if reasoning:
                reasoning_content += chunk.choices[0].delta.reasoning_content
                print(reasoning,end = '', flush = True)
            elif chunk.choices[0].delta.content:
                if book == False:
                    print("\n\nAnswer:")
                    book = True
                content += chunk.choices[0].delta.content
                print(chunk.choices[0].delta.content,end = '', flush = True)
        msg.append({"role":"assistant","content":content})

    elif Internet == True:
        Internet = False
        response = client.responses.create(
            model="deepseek-v4-flash",
            input=msg,
            stream=True,
            extra_body={"thinking": {"type": "enabled"}},
            tools = [{"type": "web_search"}]
        )

        print("Thinking:")
        for chunk in response:
            if chunk.type == "response.reasoning_text.delta":
                if book == True:
                    print("\n\nThinking:")
                    book = False
                reasoning_content += chunk.delta
                print(chunk.delta,end = "",flush = True)
            elif chunk.type == "response.output_text.delta":
                if book == False:
                    print("\n\nAnswer:")
                    book = True
                content += chunk.delta
                print(chunk.delta, end="",flush = True)
        msg.append({"role":"assistant","content":content,"reasoning_content": reasoning_content})
    
    print("\n")

