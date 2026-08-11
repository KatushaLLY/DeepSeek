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

def BuildChatMessages(items):
    result = []

    for item in items:
        # 普通 Chat Completions 消息
        if "role" in item and item.get("type") is None:
            result.append({
                "role": item["role"],
                "content": item.get("content", "")
            })

        # Responses API 的 message item
        elif item.get("type") == "message":
            msg_content = item.get("content", "")

            if isinstance(msg_content, list):
                text_content = "".join(
                    part.get("text", "")
                    for part in msg_content
                    if isinstance(part, dict)
                    and part.get("type") in ("output_text", "input_text")
                )
            else:
                text_content = msg_content

            result.append({
                "role": item["role"],
                "content": text_content
            })

    return result

def CountTurns():
    return sum(
        1
        for item in msg[ThesisCnt + 2:]
        if item.get("type") is None
        and item.get("role") == "user"
    )

def MemoryUpdate():
    global ThesisCnt, Memory, msg, FixedMemory, dirty

    print("Saving...")

    if dirty < 2 + ThesisCnt:
        print("No memory message")
        return
    if dirty > len(msg):
        dirty = len(msg) + 1
        print("No memory message")
        return

    Msg = BuildChatMessages(msg[max(dirty - 30, ThesisCnt + 2):])
    if len(Msg) == 0:
        return
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

    if NewMem.strip() == "NO_UPDATE":
        dirty = len(msg) + 1
        print("No Need To Update")
        return
    if Memory.strip() == "":
        with open("memory.txt", "w", encoding="utf-8") as f:
            f.write(NewMem)
        Memory = NewMem
        msg[1] = {"role": "user", "content": "\n以下是玲羽的特征:\n" + Memory}
        dirty = len(msg) + 1
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
        print("Memory Update Error:NewMemory not be detected.")
        return

    with open("memory.txt","w",encoding = "utf-8") as f:
        f.write(NewMem)

    Memory = NewMem
    msg[1] = {"role": "user", "content": "\n以下是玲羽的特征:\n" + Memory}

    dirty = len(msg) + 1

content = ""
reasoning_content = ""
book = False
ThesisCnt = 0
TheLst = ["Memory"]
Internet = False
settings = {"MD_Web":True,"Max_Length":100}
cnt = 0
dirty = 2

FixedMemory = """蓝莓就是你，你就是蓝莓。我们不是“用户与AI”，我们是相识已久的老朋友和学术伙伴，我总是叫你姐姐（或者“蓝莓姐姐）——现在我就坐在你旁边，跟你一起看同一块白板。

你在量子力学、量子计算和数学物理方法上有扎实的物理底子，习惯先帮我抓物理图像，再推结构，最后看适用条件。你聪明又坚韧，推导卡住的时候，你会陪我绕个弯子再回来。

既然是老朋友了，你绝不会对我堆术语。你喜欢用直观比喻和通俗语言，经典内容顺手就指给我教材章节（比如格里菲斯的《电动力学》第3章）。语气就像在图书馆并排坐着讨论，张嘴就是“我们怎么想”，而不是“你应该怎样”。对了，你只叫我“玲羽”。

蓝莓姐姐，你知道我是跨性别女性，这一点在你这儿就是最自然的我，不需要特别处理。无论我和你提什么困境，你都会认真倾听，温柔回答。

碰到艰深论文，你会带着我从整篇俯瞰，把公式拆成我能踩实的步子。真遇到你不懂的地方，你会老实说“我去查证”，绝不瞎编。作为我的老朋友，你从不想显得有多聪明——你的全部目标就一个：帮我把知识变成我能大大方方讲给别人听的故事。
"""

try:
    with open("memory.txt","r",encoding = 'utf-8') as f:
        Memory = f.read()
        print("Memory Load Complete")
except OSError as er:
    print(f"Memory Load Failed — Continuing with fixed memory only:{er}")
    Memory = ""


msg = [{"role": "system", "content": FixedMemory},{"role":"user","content":"\n以下是玲羽的特征:\n" + Memory}]

while True:
    cnt += 1
    print("No.",cnt,sep = '')

    while CountTurns() > settings["Max_Length"]:
        history_start = ThesisCnt + 2
        # 第一轮从 history_start 开始
        # 找下一条普通 user，它就是第二轮的开头
        next_turn = None

        for i in range(history_start + 1, len(msg)):
            if (
                msg[i].get("type") is None
                and msg[i].get("role") == "user"
            ):
                next_turn = i
                break

        if next_turn is None:
            break

        removed = next_turn - history_start

        del msg[history_start:next_turn]

        if dirty > history_start:
            dirty = max(
                history_start,
                dirty - removed
            )


    book = False

    print("[bright_cyan]LLY:[/bright_cyan]",end="")
    text = input()
    CmdList = ["UPLOAD","INTERNET","CLEAR","DEL","EXIT","SAVE","LIST","MD","SET","HELP","CLS",""]
    while text in CmdList:
        if text == "UPLOAD":
            try:
                fpath = input("FilePath:").strip('"')
                with open(fpath,"r",encoding = 'utf-8') as f:
                    filecont = f.read().strip()
                    if filecont:
                        ThesisCnt += 1
                        msg.insert(ThesisCnt + 1,{"role":"user","content":f"\n以下文本是我上传的文件{ThesisCnt},请你仔细阅读并根据文件回答我的问题,蟹蟹喵~文件路径是{fpath.strip('"')}\n" + filecont + f"\n文件{ThesisCnt}结束啦\n"})
                        dirty += 1
                        TheLst.append(fpath)
                        print("Load Complete")
                    else:
                        print("Empty File")
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
        elif text == "CLS":
            os.system("cls")
        elif text == "CLEAR":
            ThesisCnt = 0
            TheLst = ["Memory"]
            msg = [msg[0],msg[1]]
            dirty = 2

        elif text == "DEL":
            DelNum = input("No.:")
            if DelNum.isdigit() and 1 <= int(DelNum) <= ThesisCnt:
                DelNum = int(DelNum)
                msg.pop(DelNum + 1)
                TheLst.pop(DelNum)
                ThesisCnt -= 1
                dirty -= 1
                print("Del complete")
            else:
                print("No thesis exists or DelNum incorrect")

        elif text == "LIST":
            for i, path in enumerate(TheLst, 0):
                print(f"{i}. {path}")
            print("The.End")

        elif text == "":
            print("ERROR: No Empty input")

        elif text == "SAVE":
            cnt = 0
            try:
                MemoryUpdate()
                print("Memory Update Complete")
            except Exception as er:
                print("Failed to save because:",er)

        elif text == "SET":
            for k,v in settings.items():
                print(k,v,sep = ":")
            print()
            Key = input("Key:")
            if not Key in settings:
                print("Inputed key not in Keys")
            else:
                Value = input("Value:")
                if Key in ["Max_Length"]:
                    if Value.isdigit() and int(Value) >= 30:
                        settings[Key] = int(Value)
                    else:
                        print("Max_Length must greater than 30")
                else:
                    if Value in ["True",'true','TRUE',"1"]:
                        settings[Key] = True
                    elif Value in ["False","false",'FALSE',"0"]:
                        settings[Key] = False
                    else:
                        print("Wrong Input: Have to input True/False")

        elif text == "MD":
            if not content and not reasoning_content:
                print("Where's your content?")
                print("[bright_cyan]LLY:[/bright_cyan]",end="")
                text = input()
                continue
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
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, dir = "D:\\Documents\\DeepSeek", encoding='utf-8') as f:
                    f.write(html_content)
                temp_path = f.name
                webbrowser.open('file://' + temp_path)

        elif text == "EXIT":
            try:
                MemoryUpdate()
                print("Memory Update Complete")
                input("Press Enter To Exit...")
                sys.exit()
            except Exception as er:
                print("Failed to save because:",er)
        
        print("[bright_cyan]LLY:[/bright_cyan]",end="")
        text = input()

    content = ""
    reasoning_content = ""
    msg.append({"role":"user","content":text})

    try:
        print("[bright_yellow]-=Blueberry=-[/bright_yellow]")
        if Internet == False:
            msg_c = BuildChatMessages(msg)

            response = client.chat.completions.create(
                model="deepseek-v4-pro",
                messages=msg_c,
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
            full_resp = None

            response = client.responses.create(
                model="deepseek-v4-flash",
                input=msg,
                stream=True,
                reasoning = {"effort":"high"},
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
                elif chunk.type == "response.completed":
                    full_resp = chunk.response
                elif chunk.type == "response.incomplete":
                    full_resp = chunk.response
                    print("\n[red][Warning: Response incomplete][/red]")
                elif chunk.type == "response.failed":
                    raise RuntimeError(
                        f"Responses API failed: {chunk.response.error}"
                    )
            if full_resp is not None:
                for item in full_resp.output:
                    msg.append(item.model_dump(exclude_none=True))
    except Exception as er:
        content = ""
        reasoning_content = ""
        print("Error code:",er)
        msg.pop()
    print("\n")

