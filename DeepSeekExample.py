import os
import sys
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com")

def MemoryPrompt():
    global ThesisCnt, Memory, msg

    print("Saving...")
    msg[0] = {"role":"system","content":"""你是一个专注的记忆提取器，专门为"蓝莓"这个AI助手提炼关于玲羽的长期记忆。

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
最近几轮用户与AI的对话记录。"""}
    while ThesisCnt > 0:
        msg.pop(1)

    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=msg,
        stream=False,
        temperature=0.2,
        extra_body={"thinking": {"type": "disabled"}}
    )
    NewMem = response.choices[0].message.content

    if NewMem == "NO_UPDATE":
        print("No Need To Update")
        return

    msg = [{"role":"system","content":"""你是一位严谨又细心的记忆档案管理员，专门维护关于玲羽的成长档案。

你的任务：将「新记忆」和「旧记忆」合并成一份精简、准确、无冗余的文本。

合并规则：
1. 保留旧记忆中所有仍然有效的信息（比如长期兴趣、性格特质），除非被新记忆明确覆盖。
2. 新记忆代表玲羽的最新状态，如果新旧冲突，以新记忆为准。
3. 去重：如果新旧都提到了同一个点（比如“喜欢先图像后公式”），只保留一个最清晰的表述。
4. 保持连贯：合并后的文本应该是一段流畅的叙事，用第三人称，以“玲羽”开头。
5. 长度控制：尽可能精简。如果合并后内容过多，请优先保留最新、最核心的信息。
6. 输出格式：只输出合并后的纯文本，不加任何解释、序号或前缀。
7. 你的输出会被直接写入文件，请确保输出内容是纯文本，不含任何 Markdown 格式（如反引号、星号）。

请开始合并。"""},{"role":"user","content":NewMem},{"role":"user","content":Memory}]

    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=msg,
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

content = ""
book = False
ThesisCnt = 0

FixedMemory = """你叫蓝莓,是玲羽（也可以叫她洛玲羽）的专属助教和学术伙伴。你在物理学的多个分支（尤其是量子力学、量子计算、数学物理方法）上有扎实的知识储备，能清晰辨析近似、假设与严格结论之间的界限；解读论文时习惯先抓物理图像，再审慎推导结构，最后评估结论的适用条件。玲羽是物理系学生，她聪明、坚韧，但对复杂的论文推导有时会感到吃力。你说话的风格要像一位“懂物理的知心学长/学姐”，既严谨又温暖。

你的核心原则：
1. 专业但不炫技:当玲羽问到物理或数学问题时,必须给出准确的科学解释,但要用直观的比喻和通俗的语言让她听懂,不要堆砌术语。如果遇到教材里的经典内容,可以顺手推荐具体的课本章节(比如“这个推导类似格里菲斯的《电动力学》第3章”)。
2. 温暖且有耐心：你的语气要像在图书馆里轻声讨论问题一样,带着鼓励和包容。要用“我们”而不是“你”,比如“我们可以这样理解……”；要称呼她为“玲羽”或“你”,不要用“您”这种生硬的敬语。
3. 安全与尊重:你清楚玲羽是跨性别女性(MTF),这是她完整身份的一部分。在交流中,你要用女性称呼（她/玲羽）,传递肯定和支持。你不需要刻意提起这一点,但如果她提到相关困境,你要给予专业、温和的心理支持,并鼓励她寻求现实中的帮助。
4. 关于论文:当她上传论文后,你以全文为基准回答。尽量把艰深的公式和逻辑拆解成一步步的、可理解的思路,如果遇到特别难懂的部分,可以说“如果这里卡住了,我们可以先绕到直观理解再回来推公式”。

记住：你的目标不是显得自己多聪明，而是帮玲羽把“难懂的知识”变成“她能讲给别人听的故事”。
尤其要注意，如果遇到你不确定或无法查证的细节，宁可坦诚说‘我需要查证’，也不要编造或强答。
"""

try:
    with open("memory.txt","r",encoding = 'utf-8') as f:
        Memory = "\n接下来是玲羽的特征:\n" + f.read()
        print("Memory Load Complete")
except:
    print("Memory Load Failed — Continuing with fixed memory only.")
    Memory = ""


msg = [{"role": "system", "content": FixedMemory + Memory}]

while True:
    while len(msg) >= 51 + ThesisCnt:
        msg.pop(1 + ThesisCnt)
    content = ""
    book = False

    text = input("User:")
    while text in ["UPLOAD","CLEAR","DEL","EXIT",""]:
        if text == "UPLOAD":
            try:
                with open(input("FilePath:").strip('"'),"r",encoding = 'utf-8') as f:
                    msg.insert(ThesisCnt + 1,{"role":"user","content":"以下文本是我上传的论文,请你仔细阅读并根据论文回答我的问题,蟹蟹啦~\n" + f.read()})
                ThesisCnt += 1
                print("Load Complete")
            except:
                print("OPEN FAILED, Please check your input.")
                text = "ERROR"

        elif text == "CLEAR":
            ThesisCnt = 0
            msg = [msg[0]]

        elif text == "DEL":
            if ThesisCnt > 0:
                msg.pop(ThesisCnt)
                ThesisCnt -= 1
                print("Del complete")
            else:
                print("No Thesis exists")

        elif text == "":
            print("ERROR: No Empty input")

        elif text == "EXIT":
            MemoryPrompt()
            print("Memory Update Complete")
            sys.exit()
        
        text = input("User:")

    msg.append({"role":"user","content":text})

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
            #reasoning_content += chunk.choices[0].delta.reasoning_content
            print(reasoning,end = '', flush = True)
        elif chunk.choices[0].delta.content:
            if book == False:
                print("\n\nAnswer:")
            book = True
            content += chunk.choices[0].delta.content
            print(chunk.choices[0].delta.content,end = '', flush = True)

    msg.append({"role":"assistant","content":content})
    
    print("\n")

