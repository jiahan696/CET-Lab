"""Generated fallback copy of assets/questions.json for mobile/packaged builds.

Run tools/sync_question_data.py after editing the JSON bank.
"""
QUESTIONS_JSON = r'''{
  "meta": {
    "title": "CET Glass Lab 内置题库",
    "version": 1,
    "description": "45 道四六级真题风格题目，含单选与多选、标准答案与详细解析。",
    "counts": {"listening": 15, "reading": 20, "translation": 10}
  },
  "questions": [
    {
      "id": "L4-01",
      "level": "CET-4",
      "category": "listening",
      "type": "single",
      "section": "短对话",
      "material": "M: I need to print my presentation handout before class, but the printer in the library is out of order.\nW: The copy shop next to the east gate is still open. It's only a five-minute walk.\nM: Good. I'll head there now.",
      "question": "What will the man do?",
      "options": [
        "Wait for the library printer to be repaired.",
        "Go to a copy shop near the east gate.",
        "Borrow a printer from his classmate.",
        "Cancel his presentation for today."
      ],
      "answers": ["B"],
      "explanation": "女士明确建议去东门旁的复印店，并说步行只要五分钟；男士回答“I'll head there now”，说明他决定前往复印店。A 项与打印机故障矛盾，C、D 项均未提及。",
      "difficulty": "基础"
    },
    {
      "id": "L4-02",
      "level": "CET-4",
      "category": "listening",
      "type": "single",
      "section": "短对话",
      "material": "W: Did you catch the 8:30 bus?\nM: No, I missed it by two minutes. The next one isn't until nine, and my interview starts at 9:15.\nW: Why not take a shared bike? The company is only ten minutes away.\nM: That's a good idea.",
      "question": "How will the man probably get to the interview?",
      "options": [
        "By taxi.",
        "By subway.",
        "By shared bike.",
        "On foot."
      ],
      "answers": ["C"],
      "explanation": "男士错过公交，下一班要等到九点，而面试九点十五开始；女士建议骑共享单车，男士说“That's a good idea”，可推断他会骑共享单车前往。",
      "difficulty": "基础"
    },
    {
      "id": "L4-03",
      "level": "CET-4",
      "category": "listening",
      "type": "single",
      "section": "短篇新闻",
      "material": "The city's transport authority announced on Monday that a new night bus line will run between the central railway station and the airport. The service will operate every 30 minutes from 11 p.m. to 5 a.m. and charge a flat fare of five yuan. Officials say the route is designed for passengers on late flights and early shifts.",
      "question": "What is the purpose of the new night bus line?",
      "options": [
        "To reduce traffic during rush hours.",
        "To serve late-night travelers and workers.",
        "To replace the airport train service.",
        "To carry tourists to the city center."
      ],
      "answers": ["B"],
      "explanation": "新闻最后一句指出，这条线路是为乘坐深夜航班和上早班的乘客设计的（passengers on late flights and early shifts），因此 B 项最准确。A、C、D 项均未在材料中提及。",
      "difficulty": "基础"
    },
    {
      "id": "L4-04",
      "level": "CET-4",
      "category": "listening",
      "type": "single",
      "section": "短对话",
      "material": "W: Professor Lee, I'd like to discuss my term paper. Are you available on Wednesday afternoon?\nM: I have a faculty meeting then. My office hours have moved to Thursday, two to four. Just drop by with your outline.\nW: Great, I'll be there.",
      "question": "When can the woman meet Professor Lee?",
      "options": [
        "On Wednesday morning.",
        "On Wednesday afternoon.",
        "On Thursday morning.",
        "On Thursday afternoon."
      ],
      "answers": ["D"],
      "explanation": "教授说明办公时间已改到星期四下午两点到四点（Thursday, two to four），女士回答会过去。因此见面时间是周四下午，选 D。",
      "difficulty": "基础"
    },
    {
      "id": "L4-05",
      "level": "CET-4",
      "category": "listening",
      "type": "single",
      "section": "长对话",
      "material": "M: Congratulations on getting the offer from the marketing firm. Are you going to accept it?\nW: I'm still thinking. The salary is good, but I'm not sure about the training. The job description says new employees receive six weeks of training.\nM: That's actually a strong point. You'll learn their systems before you start.\nW: You're right. I'll ask whether the training is paid, and then decide.",
      "question": "What will the woman probably do next?",
      "options": [
        "Decline the offer immediately.",
        "Ask about the training conditions.",
        "Request a much higher salary.",
        "Contact the marketing manager."
      ],
      "answers": ["B"],
      "explanation": "女士对培训安排仍不确定，最后明确说会先询问培训是否带薪（whether the training is paid），再做决定。因此她下一步最可能了解培训条件，选 B。",
      "difficulty": "进阶"
    },
    {
      "id": "L4-06",
      "level": "CET-4",
      "category": "listening",
      "type": "single",
      "section": "短篇新闻",
      "material": "Volunteers in the coastal town collected more than two tons of plastic waste from the beach last weekend. The cleanup was organized by a local environmental group, which plans to hold similar events every month. Organizers say the waste will be sorted and sent to a recycling center, while reusable items will be donated.",
      "question": "What will happen to the reusable items?",
      "options": [
        "They will be sold online.",
        "They will be sent to a recycling center.",
        "They will be stored by the local government.",
        "They will be donated."
      ],
      "answers": ["D"],
      "explanation": "新闻最后一句说垃圾会分类后送往回收中心，而可再利用的物品会被捐赠（reusable items will be donated）。注意区分 recycling center 对应的是 waste，不是 reusable items。",
      "difficulty": "基础"
    },
    {
      "id": "L4-07",
      "level": "CET-4",
      "category": "listening",
      "type": "single",
      "section": "短文理解",
      "material": "Researchers at a university sleep center monitored 300 students for four weeks. They found that students who used their phones for more than an hour before bed took about 25 minutes longer to fall asleep than those who did not. The researchers suggest keeping phones outside the bedroom and reading a paper book instead.",
      "question": "What do the researchers suggest?",
      "options": [
        "Keeping phones outside the bedroom.",
        "Going to bed at an earlier time.",
        "Using phones for less than two hours a day.",
        "Reading the news before sleeping."
      ],
      "answers": ["A"],
      "explanation": "研究结论后的建议是“keeping phones outside the bedroom and reading a paper book instead”，即把手机放在卧室外、改读纸质书。A 项直接对应原文；B、C、D 均未提到。",
      "difficulty": "基础"
    },
    {
      "id": "L4-08",
      "level": "CET-4",
      "category": "listening",
      "type": "single",
      "section": "短对话",
      "material": "W: I'm interested in the apartment on Green Street. Does the rent include utilities?\nM: It includes internet and water, but electricity is billed separately. The average electricity cost in winter is about 80 yuan a month.\nW: I see. That's still within my budget.",
      "question": "What is included in the rent?",
      "options": [
        "Internet and electricity.",
        "Water and electricity.",
        "Internet and water.",
        "All utilities."
      ],
      "answers": ["C"],
      "explanation": "男士说房租包含网络和水费（includes internet and water），电费另计。因此 C 项正确。听到“but electricity is billed separately”即可排除含电费的选项。",
      "difficulty": "基础"
    },
    {
      "id": "L6-01",
      "level": "CET-6",
      "category": "listening",
      "type": "single",
      "section": "讲座",
      "material": "Today we'll look at the default effect in behavioral economics. When people are automatically enrolled in a retirement savings plan, participation rises sharply compared with systems where they must sign up themselves. The lesson is not that people are lazy, but that the effort of making a decision can prevent action. Policymakers can therefore improve outcomes by changing the default, while still allowing people to opt out.",
      "question": "What does the speaker say about the default effect?",
      "options": [
        "It proves that most people are lazy.",
        "It only works in retirement planning.",
        "It can raise participation without removing choice.",
        "It forces people to make better decisions."
      ],
      "answers": ["C"],
      "explanation": "讲座指出，自动加入能显著提高参与率，同时仍然允许人们选择退出（while still allowing people to opt out）。这说明默认选项可以在不剥夺选择权的情况下改善结果，C 正确。讲话者还明确否认“人们懒惰”的解释。",
      "difficulty": "进阶"
    },
    {
      "id": "L6-02",
      "level": "CET-6",
      "category": "listening",
      "type": "single",
      "section": "长对话",
      "material": "M: Your paper's sample is only 30 participants. Isn't that too small?\nW: For a qualitative study, the goal isn't statistical generalization. I'm looking at how individuals describe their experience, so I interviewed each participant three times.\nM: Then you should explain that in the methods section.",
      "question": "What does the woman imply about her sample size?",
      "options": [
        "It is larger than most studies in the field.",
        "It is appropriate for qualitative research.",
        "It should be doubled before publication.",
        "It was chosen by her supervisor."
      ],
      "answers": ["B"],
      "explanation": "女士说定性研究的目标不是统计上的推广，而是了解个体如何描述自己的经历，因此她更看重访谈深度（每人三次）。她的言下之意是 30 人的样本对定性研究是合适的，B 正确。",
      "difficulty": "进阶"
    },
    {
      "id": "L6-03",
      "level": "CET-6",
      "category": "listening",
      "type": "single",
      "section": "短篇新闻",
      "material": "A new artificial intelligence system developed by European meteorologists can predict heavy rainfall up to six hours earlier than conventional models. In a trial covering five countries, the system reduced false alarms by 18 percent. Researchers stress that human forecasters will remain essential for issuing public warnings.",
      "question": "What is one benefit of the new AI system?",
      "options": [
        "It predicts heavy rain earlier than conventional models.",
        "It has replaced human weather forecasters.",
        "It eliminates all false weather alarms.",
        "It works only in five European cities."
      ],
      "answers": ["A"],
      "explanation": "新闻首句指出，该系统能比传统模型提前最多六小时预测暴雨。它减少误报 18%，但并未完全消除误报，也没有取代人类预报员，因此 B、C 错；试验覆盖五个国家而非五个城市，D 也错。",
      "difficulty": "进阶"
    },
    {
      "id": "L6-04",
      "level": "CET-6",
      "category": "listening",
      "type": "single",
      "section": "讲座",
      "material": "Urban green spaces do more than beautify cities. Trees and parks can lower surface temperatures by several degrees, reducing the demand for air conditioning. They also absorb rainwater, which helps prevent flooding. But benefits depend on how green spaces are designed and maintained; a small patch of grass provides far less cooling than a mature tree canopy.",
      "question": "What does the speaker emphasize about urban green spaces?",
      "options": [
        "They are mainly valuable for their beauty.",
        "They always reduce flooding completely.",
        "They are cheaper than air conditioning.",
        "Their benefits depend on design and maintenance."
      ],
      "answers": ["D"],
      "explanation": "讲话者列举了降温、减少空调需求和吸收雨水等好处后，用 But 转折强调：收益取决于绿地如何设计和维护。草地与成熟树冠的降温效果差异就是例证，因此 D 正确。",
      "difficulty": "进阶"
    },
    {
      "id": "L6-05",
      "level": "CET-6",
      "category": "listening",
      "type": "single",
      "section": "长对话",
      "material": "W: How did your presentation go?\nM: The talk itself was fine, but the question-and-answer session caught me off guard. Someone asked about the long-term cost, and I didn't have the figures with me.\nW: Next time, prepare a backup slide with likely questions and key numbers.",
      "question": "What does the woman suggest the man do?",
      "options": [
        "Avoid answering difficult questions.",
        "Shorten his next presentation.",
        "Prepare backup material for the Q&A.",
        "Ask a colleague to attend with him."
      ],
      "answers": ["C"],
      "explanation": "女士建议他下次准备一张备用幻灯片，列出可能被问到的问题和关键数字（prepare a backup slide with likely questions and key numbers），即提前准备问答环节的备用材料，C 正确。",
      "difficulty": "进阶"
    },
    {
      "id": "L6-06",
      "level": "CET-6",
      "category": "listening",
      "type": "single",
      "section": "短篇新闻",
      "material": "A national museum has agreed to return a ceremonial mask to the country where it was made more than a century ago. The mask was acquired by a private collector during the colonial period and donated to the museum in 1958. Museum officials said the return is part of a broader effort to address contested collections and deepen cooperation with the originating community.",
      "question": "Why is the museum returning the mask?",
      "options": [
        "The mask is no longer valuable.",
        "To address the history of contested collections.",
        "The museum needs space for new exhibits.",
        "The mask was damaged and cannot be repaired."
      ],
      "answers": ["B"],
      "explanation": "博物馆官员说，归还文物是“address contested collections”的更大努力的一部分，即回应有争议的收藏来源问题，并加强与原属社区的合作。B 项直接概括这一原因。",
      "difficulty": "进阶"
    },
    {
      "id": "L6-07",
      "level": "CET-6",
      "category": "listening",
      "type": "single",
      "section": "讲座",
      "material": "Memory is not a recording stored in a single place. Each time we recall an event, the memory can become temporarily unstable before being reconsolidated. This process allows new information to be integrated, but it also means that a memory can be altered. In one experiment, participants who were asked to recall a car accident later remembered details differently from those who were not.",
      "question": "What does the car accident experiment show?",
      "options": [
        "People cannot remember accidents accurately.",
        "Memories disappear if they are not recalled.",
        "Recalling an event can change the memory.",
        "New information always improves memory."
      ],
      "answers": ["C"],
      "explanation": "讲座指出回忆会让记忆暂时不稳定，在再巩固过程中可能被改变；车祸实验正是例证：被要求回忆的人后来记住的细节与未被要求者不同。因此 C 正确。A 项扩大了结论，B、D 与材料不符。",
      "difficulty": "挑战"
    },
    {
      "id": "R4-01",
      "level": "CET-4",
      "category": "reading",
      "type": "single",
      "section": "仔细阅读",
      "material": "At many universities, student volunteers run free tutoring programs for children in nearby communities. The programs are popular not only because they help children, but also because they give university students practical experience. Volunteers receive training in lesson planning and classroom management before they begin. Most commit two hours a week for a semester. Organizers say the biggest challenge is not finding children who need help, but retaining volunteers during exam periods.",
      "question": "What is the biggest challenge for the tutoring programs?",
      "options": [
        "Finding children who need help.",
        "Keeping volunteers during exam periods.",
        "Training volunteers to plan lessons.",
        "Persuading universities to provide funding."
      ],
      "answers": ["B"],
      "explanation": "文章最后一句明确指出：最大的挑战不是找到需要帮助的孩子，而是在考试期间留住志愿者（retaining volunteers during exam periods）。B 项是同义转述。",
      "difficulty": "基础"
    },
    {
      "id": "R4-02",
      "level": "CET-4",
      "category": "reading",
      "type": "single",
      "section": "仔细阅读",
      "material": "Some companies have introduced 'quiet hours' during which employees are asked not to send internal messages outside working time. The policy is meant to reduce stress and protect employees' ability to rest. However, critics note that quiet hours can simply push work into the daytime, making employees more rushed. For the policy to work, managers must also model the behavior and avoid sending messages themselves.",
      "question": "What is necessary for quiet hours to work?",
      "options": [
        "Employees must work longer hours.",
        "Companies must ban all internal messages.",
        "Managers must set an example.",
        "The policy must apply only to new employees."
      ],
      "answers": ["C"],
      "explanation": "最后一句说，为了让该政策奏效，管理者也必须以身作则，避免自己发消息（managers must also model the behavior）。C 项“管理者必须树立榜样”是同义表达。",
      "difficulty": "基础"
    },
    {
      "id": "R4-03",
      "level": "CET-4",
      "category": "reading",
      "type": "single",
      "section": "仔细阅读",
      "material": "An increasing number of supermarkets are selling 'imperfect' fruit and vegetables at lower prices. These products are safe and nutritious but do not meet the cosmetic standards of large retailers. Supporters say the initiative reduces waste and helps consumers save money. Some shoppers remain hesitant, however, because they associate unusual shapes with poor quality. Education campaigns are therefore as important as price discounts.",
      "question": "Why are some shoppers hesitant to buy imperfect produce?",
      "options": [
        "They believe it is not nutritious.",
        "They think unusual shapes mean poor quality.",
        "They are worried about the price.",
        "They prefer imported fruit and vegetables."
      ],
      "answers": ["B"],
      "explanation": "文中说一些顾客犹豫，是因为他们把不寻常的外形与质量差联系起来（associate unusual shapes with poor quality）。B 项直接对应。文章已说明这些产品安全且有营养，A 错。",
      "difficulty": "基础"
    },
    {
      "id": "R4-04",
      "level": "CET-4",
      "category": "reading",
      "type": "single",
      "section": "仔细阅读",
      "material": "Remote work can save employees commuting time, but it can also blur the boundary between work and personal life. A survey of 1,200 office workers found that those working from home were more likely to answer messages after dinner. Researchers recommend setting a fixed end time for work and creating a separate workspace, even if it is only a corner of a room.",
      "question": "What do researchers recommend for remote workers?",
      "options": [
        "Setting a fixed end time for work.",
        "Avoiding all messages after lunch.",
        "Working from a separate apartment.",
        "Returning to the office several days a week."
      ],
      "answers": ["A"],
      "explanation": "研究人员建议设定固定的工作结束时间（setting a fixed end time for work），并创造独立的工作空间。A 项直接对应；文中只说 even if it is only a corner of a room，并未要求单独公寓。",
      "difficulty": "基础"
    },
    {
      "id": "R4-05",
      "level": "CET-4",
      "category": "reading",
      "type": "multiple",
      "section": "多项选择",
      "material": "A study of first-year students identified three habits linked to better exam performance: spacing study sessions across several days, testing oneself instead of rereading notes, and explaining concepts to someone else. The study found no significant benefit from studying in the same place every day. It also found that students who studied mostly at night did not perform better or worse than morning studiers.",
      "question": "Which TWO habits were linked to better exam performance?",
      "options": [
        "Spacing study sessions across several days.",
        "Studying in the same place every day.",
        "Testing oneself instead of rereading notes.",
        "Studying mainly at night."
      ],
      "answers": ["A", "C"],
      "explanation": "文章列出三个与更好成绩相关的习惯：间隔学习、自我测试、向他人解释概念。A、C 分别对应前两个。每天在同一地点学习和夜间学习均被研究明确排除，B、D 错。",
      "difficulty": "基础"
    },
    {
      "id": "R4-06",
      "level": "CET-4",
      "category": "reading",
      "type": "single",
      "section": "仔细阅读",
      "material": "Electric bicycles are becoming a common sight in many cities. They are faster than ordinary bikes and require less effort, which makes them attractive to commuters. Safety experts warn, however, that higher speeds increase the risk of crashes, especially on shared paths. Several cities are now considering speed limits and mandatory helmets for e-bike riders.",
      "question": "What are several cities considering?",
      "options": [
        "Banning e-bikes from all roads.",
        "Requiring riders to take a test.",
        "Setting speed limits and requiring helmets.",
        "Building separate paths for e-bikes."
      ],
      "answers": ["C"],
      "explanation": "文章最后一句说，多个城市正在考虑限速和强制佩戴头盔（speed limits and mandatory helmets）。C 项完全对应，其他选项均未提及。",
      "difficulty": "基础"
    },
    {
      "id": "R4-07",
      "level": "CET-4",
      "category": "reading",
      "type": "single",
      "section": "仔细阅读",
      "material": "Teenagers need about eight to ten hours of sleep each night, yet many get far less. Experts say that delaying school start times can help, because adolescents' natural sleep rhythms shift later during puberty. In districts that moved start times from 7:30 to 8:30, students reported better attention and fewer absences. Critics worry about bus schedules and after-school activities, but supporters argue that the academic benefits outweigh the logistical costs.",
      "question": "What did districts that delayed school start times report?",
      "options": [
        "Longer school days.",
        "More after-school activities.",
        "Fewer teachers absent.",
        "Better attention and fewer absences."
      ],
      "answers": ["D"],
      "explanation": "文中说，将上课时间从 7:30 推迟到 8:30 的学区报告学生注意力更好、缺勤更少（better attention and fewer absences）。D 项直接对应。",
      "difficulty": "基础"
    },
    {
      "id": "R4-08",
      "level": "CET-4",
      "category": "reading",
      "type": "multiple",
      "section": "多项选择",
      "material": "Museum membership offers more than free admission. Members often receive invitations to previews of new exhibitions, discounts in the gift shop, and access to lectures by curators. Some museums also allow members to bring a guest for free. However, special evening events and behind-the-scenes tours usually require an additional fee, even for members.",
      "question": "Which TWO benefits are included with museum membership?",
      "options": [
        "Free admission.",
        "Free guest admission at all museums.",
        "Invitations to exhibition previews.",
        "Free behind-the-scenes tours."
      ],
      "answers": ["A", "C"],
      "explanation": "文章开头说会员福利不止免费入场，并列出新展预览邀请、礼品店折扣和策展人讲座。A、C 正确。幕后参观通常需额外付费，D 错；免费携客只是“Some museums”提供，B 的 at all museums 过于绝对。",
      "difficulty": "基础"
    },
    {
      "id": "R4-09",
      "level": "CET-4",
      "category": "reading",
      "type": "single",
      "section": "仔细阅读",
      "material": "Public libraries are adapting to changing needs. Besides lending books, many now offer free Wi-Fi, meeting rooms, and classes in digital skills. Some libraries have added tool-lending programs, allowing residents to borrow items such as drills and sewing machines. Librarians say these services bring in people who might never have used a library before, but they also require new funding and staff training.",
      "question": "What challenge do the new library services bring?",
      "options": [
        "Fewer people borrowing books.",
        "A need for funding and staff training.",
        "A shortage of meeting rooms.",
        "Complaints from local businesses."
      ],
      "answers": ["B"],
      "explanation": "最后一句指出，新服务虽然吸引了以前不用图书馆的人，但也需要新的资金和员工培训（require new funding and staff training）。B 项直接对应。",
      "difficulty": "基础"
    },
    {
      "id": "R4-10",
      "level": "CET-4",
      "category": "reading",
      "type": "single",
      "section": "仔细阅读",
      "material": "Recycling rates vary widely between neighborhoods, even within the same city. Researchers found that the strongest predictor of participation was not income or education, but how easy the recycling system was to use. Buildings with clear labels and bins on every floor recycled far more than those with a single bin in the basement. The lesson is simple: convenience matters.",
      "question": "What was the strongest predictor of recycling participation?",
      "options": [
        "Residents' income.",
        "Residents' education level.",
        "The convenience of the recycling system.",
        "The size of the neighborhood."
      ],
      "answers": ["C"],
      "explanation": "文中明确说，最强的预测因素不是收入或教育，而是回收系统使用的便利程度（how easy the recycling system was to use）。C 项是同义概括。",
      "difficulty": "基础"
    },
    {
      "id": "R6-01",
      "level": "CET-6",
      "category": "reading",
      "type": "single",
      "section": "仔细阅读",
      "material": "The attention economy treats human attention as a scarce resource to be bought and sold. Platforms design interfaces to maximize time on site, often using infinite scroll and personalized notifications. Critics argue that this business model undermines users' ability to choose how to spend their time. Defenders respond that users can always log off. That defense is technically true but overlooks the asymmetry between sophisticated persuasion systems and individual willpower.",
      "question": "What is the author's view of the defense that users can log off?",
      "options": [
        "It is completely false.",
        "It proves that platforms are harmless.",
        "It ignores the power imbalance between platforms and users.",
        "It is the strongest argument for the attention economy."
      ],
      "answers": ["C"],
      "explanation": "作者说这一辩护“technically true but overlooks the asymmetry between sophisticated persuasion systems and individual willpower”，即它忽视了平台精心设计的说服系统与个人意志力之间的不对称。C 项准确。作者并未说它完全错误，A 过强。",
      "difficulty": "进阶"
    },
    {
      "id": "R6-02",
      "level": "CET-6",
      "category": "reading",
      "type": "single",
      "section": "仔细阅读",
      "material": "Urban agriculture is often celebrated for shortening food supply chains and greening cities. Yet its environmental benefits are not automatic. Crops grown on rooftops may require energy-intensive irrigation, and soil in some vacant lots can be contaminated. Researchers argue that urban farms should be evaluated over their full life cycle, including transport, water, and energy use, rather than assumed to be sustainable because they are local.",
      "question": "What do researchers argue about urban farms?",
      "options": [
        "They are always more sustainable than rural farms.",
        "Their full environmental impact should be assessed.",
        "They should not be allowed on rooftops.",
        "They use less water than traditional farms."
      ],
      "answers": ["B"],
      "explanation": "研究人员主张对城市农场进行全生命周期评估，把运输、水和能源使用都纳入考量，而不是因为“本地”就假定其可持续。B 项准确。文章只在某些情况下提到屋顶灌溉耗能，并未全面禁止，C 错。",
      "difficulty": "进阶"
    },
    {
      "id": "R6-03",
      "level": "CET-6",
      "category": "reading",
      "type": "single",
      "section": "仔细阅读",
      "material": "When a language disappears, it is not only words that are lost. Knowledge about local plants, weather patterns, and oral history may disappear with it. Linguists working with endangered language communities increasingly emphasize documentation and revitalization rather than simply recording grammar. Successful projects often involve community members as researchers and teachers, ensuring that the language has a future, not just an archive.",
      "question": "What do successful language projects emphasize?",
      "options": [
        "Recording grammar only.",
        "Keeping the language out of schools.",
        "Hiring foreign linguists.",
        "Community participation."
      ],
      "answers": ["D"],
      "explanation": "文中说成功的项目通常让社区成员作为研究者和教师参与（involve community members as researchers and teachers），从而让语言有未来，而不仅仅是一份档案。D 项正确。",
      "difficulty": "进阶"
    },
    {
      "id": "R6-04",
      "level": "CET-6",
      "category": "reading",
      "type": "single",
      "section": "仔细阅读",
      "material": "Carbon labels on food products aim to help consumers make climate-friendly choices. Evidence suggests, however, that labels alone have modest effects. Consumers may not understand the numbers, and price remains a stronger influence. Researchers recommend combining labels with changes in default options, such as placing low-carbon meals first on menus, so that sustainable choices become easier rather than merely more visible.",
      "question": "What do researchers recommend?",
      "options": [
        "Combining carbon labels with easier default choices.",
        "Removing prices from food products.",
        "Making carbon labels mandatory for all foods.",
        "Focusing only on consumer education."
      ],
      "answers": ["A"],
      "explanation": "研究建议把碳标签与默认选项的改变结合起来，例如把低碳餐放在菜单前面，让可持续选择更容易，而不只是更显眼。A 项准确。",
      "difficulty": "进阶"
    },
    {
      "id": "R6-05",
      "level": "CET-6",
      "category": "reading",
      "type": "multiple",
      "section": "多项选择",
      "material": "Open science advocates argue that research data and publications should be freely accessible. Benefits include faster replication and greater public trust. But openness raises concerns about privacy and about researchers being scooped before they publish. Many journals now require data availability statements, while allowing sensitive data to be shared under controlled access. The debate is therefore less about whether to be open than about how to balance openness with legitimate constraints.",
      "question": "Which TWO concerns about open science are mentioned?",
      "options": [
        "Privacy risks.",
        "Lack of public interest.",
        "Researchers being scooped.",
        "Journal rejection."
      ],
      "answers": ["A", "C"],
      "explanation": "文章明确提到开放科学引发两类担忧：隐私问题（privacy）和研究者在发表前被他人抢先（being scooped）。A、C 正确。B、D 未被提及。",
      "difficulty": "进阶"
    },
    {
      "id": "R6-06",
      "level": "CET-6",
      "category": "reading",
      "type": "single",
      "section": "仔细阅读",
      "material": "Employers increasingly use algorithms to screen job applications. Such tools can reduce the time spent on initial reviews, but they may also reproduce historical bias. For example, a system trained on past hiring decisions may favor candidates who resemble previous employees. Auditing the data and testing outcomes across groups are essential. Yet audits alone cannot settle the larger question of which criteria should matter in hiring.",
      "question": "What is the limitation of audits mentioned in the passage?",
      "options": [
        "They are too expensive for most employers.",
        "They cannot improve the training data.",
        "They cannot decide which hiring criteria are appropriate.",
        "They are illegal in many countries."
      ],
      "answers": ["C"],
      "explanation": "文章最后一句说，审计本身无法解决更大的问题：招聘中究竟应采用哪些标准（which criteria should matter in hiring）。C 项准确。A、B、D 均未提及。",
      "difficulty": "进阶"
    },
    {
      "id": "R6-07",
      "level": "CET-6",
      "category": "reading",
      "type": "single",
      "section": "仔细阅读",
      "material": "Space debris poses a growing risk to satellites. Even a small fragment can damage a spacecraft because of its high speed. Tracking systems can detect larger objects, but many pieces are too small to monitor. Engineers are testing ways to remove defunct satellites from orbit, yet international cooperation is complicated by questions of ownership and liability. Without clearer rules, cleanup remains expensive and uncertain.",
      "question": "Why is international cooperation on space cleanup complicated?",
      "options": [
        "No country has the necessary technology.",
        "Questions of ownership and liability remain unresolved.",
        "Satellites cannot be tracked at all.",
        "Space debris is no longer a serious problem."
      ],
      "answers": ["B"],
      "explanation": "文中指出，国际合作因所有权和责任归属问题而复杂（questions of ownership and liability）。B 项直接对应。追踪系统可以探测较大物体，C 说完全无法追踪，错误。",
      "difficulty": "进阶"
    },
    {
      "id": "R6-08",
      "level": "CET-6",
      "category": "reading",
      "type": "multiple",
      "section": "多项选择",
      "material": "Psychological resilience is often misunderstood as the ability to endure hardship without help. In fact, research shows that resilient people tend to use social support, adjust their plans when circumstances change, and treat setbacks as information rather than personal failure. Resilience is not a fixed trait; it can be strengthened through practice and supportive relationships.",
      "question": "Which TWO statements reflect resilience research?",
      "options": [
        "Resilience means never asking for help.",
        "Resilient people use social support.",
        "Resilience is fixed at birth.",
        "Resilience can be strengthened."
      ],
      "answers": ["B", "D"],
      "explanation": "研究指出，有韧性的人会利用社会支持，而且韧性不是固定特质，可以通过练习和支持性关系增强。B、D 正确。A 恰是文章开头的误解；C 与“not a fixed trait”矛盾。",
      "difficulty": "进阶"
    },
    {
      "id": "R6-09",
      "level": "CET-6",
      "category": "reading",
      "type": "single",
      "section": "仔细阅读",
      "material": "Research on longevity has shifted from single 'magic' foods to patterns of living. Large studies consistently associate longer, healthier lives with regular physical activity, strong social connections, and diets rich in plants. No single supplement has been shown to reproduce these effects. Scientists caution that observational studies cannot prove causation, but the consistency of findings across populations is striking.",
      "question": "What does research on longevity suggest?",
      "options": [
        "A single superfood can extend life.",
        "Lifestyle patterns matter more than single foods.",
        "Supplements are the most reliable solution.",
        "Observational studies prove causation."
      ],
      "answers": ["B"],
      "explanation": "文章说长寿研究已从单一“神奇”食物转向生活方式模式，规律运动、社会联系和植物性饮食与更长寿健康相关。B 正确。文章明确说没有单一补充剂能复制这些效果，C 错；观察性研究不能证明因果，D 错。",
      "difficulty": "挑战"
    },
    {
      "id": "R6-10",
      "level": "CET-6",
      "category": "reading",
      "type": "single",
      "section": "仔细阅读",
      "material": "Digitizing cultural heritage can make collections available to people who cannot visit in person. High-resolution images and 3D models allow researchers to study objects without handling them. Yet digitization is not a neutral act: choices about lighting, framing, and metadata shape how objects are understood. Museums must therefore treat digital records as interpretations, not transparent copies, and involve source communities in decisions about access.",
      "question": "What does the author say about digital records of cultural objects?",
      "options": [
        "They are transparent copies of the originals.",
        "They remove the need for museums.",
        "They are interpretations shaped by curatorial choices.",
        "They should not be shared with the public."
      ],
      "answers": ["C"],
      "explanation": "作者指出数字化并非中立行为，灯光、取景和元数据等选择会影响人们对文物的理解，因此数字记录应被视为一种诠释，而非透明复制品。C 正确。",
      "difficulty": "挑战"
    },
    {
      "id": "T4-01",
      "level": "CET-4",
      "category": "translation",
      "type": "single",
      "section": "译文辨析",
      "material": "茶在中国文化中占有重要地位。人们不仅在日常生活中饮茶，也常以茶待客。",
      "question": "Choose the best English translation.",
      "options": [
        "Tea plays an important role in Chinese culture. People not only drink it in daily life but also often serve it to guests.",
        "Tea is playing important role in Chinese culture, and people often use tea to entertain guests in daily life.",
        "Tea occupies important position in Chinese culture. People not only drink tea in daily life, but also often treat guests with tea.",
        "Tea is important in Chinese culture, so people drink tea every day and welcome guests by tea."
      ],
      "answers": ["A"],
      "explanation": "A 项准确传达“占有重要地位”和“不仅……也……”的递进关系，play an important role in、serve tea to guests 搭配自然。B 项 role 前缺冠词，且逻辑关系被弱化；C 项 position 前缺冠词，treat guests with tea 不如 serve tea to guests 地道；D 项“welcome guests by tea”介词错误，且因果逻辑原文没有。",
      "difficulty": "基础"
    },
    {
      "id": "T4-02",
      "level": "CET-4",
      "category": "translation",
      "type": "single",
      "section": "译文辨析",
      "material": "中国高铁网络不断扩展，使人们能够在数小时内往返于相隔很远的城市之间。",
      "question": "Choose the best English translation.",
      "options": [
        "China's high-speed rail network is expanding, which makes people possible to travel between distant cities within hours.",
        "The expanding high-speed rail network in China allows people to travel between distant cities within hours.",
        "China's high-speed rail network expands constantly so that people can go back and forth among cities which are very far away in several hours.",
        "The high-speed rail network of China is expanding and enables people traveling between cities far away within hours."
      ],
      "answers": ["B"],
      "explanation": "B 项用 The expanding ... network 简洁表达“不断扩展”，allow people to travel 搭配正确，within hours 对应“数小时内”。A 项 makes people possible 结构错误；C 项 among cities 使用不当，in several hours 位置含糊；D 项 enables people traveling 应改为 to travel。",
      "difficulty": "基础"
    },
    {
      "id": "T4-03",
      "level": "CET-4",
      "category": "translation",
      "type": "single",
      "section": "译文辨析",
      "material": "共享单车为短途出行提供了便利，但也给城市管理带来了新的挑战。",
      "question": "Choose the best English translation.",
      "options": [
        "Shared bikes provide convenience for short trips, but also bring new challenges to city management.",
        "Shared bikes make short trips convenient, but they have also brought new challenges to urban management.",
        "Shared bicycles offer convenient to short-distance travel, and also give city management new challenge.",
        "Shared bikes are convenient for short trips, but bring new challenge for the city to manage."
      ],
      "answers": ["B"],
      "explanation": "B 项时态和搭配都自然：make short trips convenient、bring challenges to urban management。A 项 provide convenience for 可以但表达略生硬，且缺少 they；C 项 offer convenient 词性错误，challenge 缺复数；D 项 bring challenge for the city to manage 结构不自然。",
      "difficulty": "基础"
    },
    {
      "id": "T4-04",
      "level": "CET-4",
      "category": "translation",
      "type": "multiple",
      "section": "多项选择",
      "material": "春节是中国最重要的传统节日，家人通常会团聚在一起吃年夜饭。",
      "question": "Which TWO translations are acceptable?",
      "options": [
        "The Spring Festival is China's most important traditional festival, and families usually get together for a reunion dinner.",
        "The Spring Festival is the most important traditional festival in China; family members usually gather to have the New Year's Eve dinner.",
        "The Spring Festival is China's most important traditional festival, families usually get together and eat a reunion dinner.",
        "The Spring Festival is China's most important traditional holiday, and family members usually gather together to eat a dinner of the year."
      ],
      "answers": ["A", "B"],
      "explanation": "A、B 两项都准确表达“最重要的传统节日”和“团聚吃年夜饭”，用词与句式均可接受。C 项两个完整句之间只用逗号，构成 comma splice；D 项 a dinner of the year 不是“年夜饭”的规范表达。",
      "difficulty": "进阶"
    },
    {
      "id": "T4-05",
      "level": "CET-4",
      "category": "translation",
      "type": "single",
      "section": "译文辨析",
      "material": "移动支付已经融入人们的日常生活，购物、乘车和缴费都可以用手机完成。",
      "question": "Choose the best English translation.",
      "options": [
        "Mobile payment has become part of daily life; people can shop, take public transport and pay bills with their phones.",
        "Mobile payment has integrated into people's daily life, shopping, taking buses and paying fees can be finished by mobile phone.",
        "Mobile payment is becoming people's daily life, and people can use phone to do shopping, take cars and pay money.",
        "Mobile payment has entered daily life of people, so shopping, taking transportation and paying bills can use mobile phones."
      ],
      "answers": ["A"],
      "explanation": "A 项用 has become part of daily life 准确表达“融入日常生活”，三个动作用 shop, take public transport and pay bills 并列，简洁自然。B 项 integrated into 缺 been，且后半句逗号连接两个完整句；C 项 is becoming people's daily life 语义错误；D 项 paying bills can use mobile phones 主语错误。",
      "difficulty": "基础"
    },
    {
      "id": "T6-01",
      "level": "CET-6",
      "category": "translation",
      "type": "single",
      "section": "译文辨析",
      "material": "乡村振兴不仅意味着改善基础设施，也意味着为年轻人创造更多在家乡发展的机会。",
      "question": "Choose the best English translation.",
      "options": [
        "Rural revitalization means not only improving infrastructure but also creating more opportunities for young people to develop in their hometowns.",
        "Rural revitalization not only means to improve infrastructure, but also means to create more opportunities for young people developing at hometown.",
        "Rural revitalization means improving infrastructure and also means create more chances for young people to develop in their home town.",
        "Rural revitalization is not only meaning to improve infrastructure, but also creating more opportunities for young people's development in hometown."
      ],
      "answers": ["A"],
      "explanation": "A 项用 not only ... but also ... 连接两个动名词，结构平行，develop in their hometowns 自然准确。B 项 means to improve 不如 means improving 贴切，developing at hometown 搭配错误；C 项 means create 缺 to；D 项 is not only meaning 时态和结构都不自然。",
      "difficulty": "进阶"
    },
    {
      "id": "T6-02",
      "level": "CET-6",
      "category": "translation",
      "type": "single",
      "section": "译文辨析",
      "material": "可持续发展要求在经济增长与环境保护之间取得平衡，而不能以牺牲后代的需求为代价。",
      "question": "Choose the best English translation.",
      "options": [
        "Sustainable development requires a balance between economic growth and environmental protection rather than sacrificing the needs of future generations.",
        "Sustainable development requires to balance economic growth and environmental protection, but not sacrifice future generations' needs.",
        "Sustainable development demands people balance between economic growth and environmental protection instead of sacrificing the needs of the future generation.",
        "Sustainable development requires balance economic growth with environmental protection rather than sacrifice the needs of future generations."
      ],
      "answers": ["A"],
      "explanation": "A 项 require a balance between ... and ... 搭配准确，rather than sacrificing 与前面的名词性结构呼应，语义清晰。B 项 require to balance 应改为 require balancing；C 项 demands people balance 缺 to；D 项 require balance economic growth 结构错误。",
      "difficulty": "进阶"
    },
    {
      "id": "T6-03",
      "level": "CET-6",
      "category": "translation",
      "type": "multiple",
      "section": "多项选择",
      "material": "非物质文化遗产的保护需要社区参与，因为许多传统技艺只有在日常生活中不断实践才能延续。",
      "question": "Which TWO translations are acceptable?",
      "options": [
        "The protection of intangible cultural heritage requires community participation, because many traditional skills can survive only through constant practice in daily life.",
        "Protecting intangible cultural heritage calls for community involvement, as many traditional crafts can be kept alive only when they are practiced continuously in everyday life.",
        "The protection of intangible cultural heritage needs communities to participate, because many traditional skills only can continue if practice in daily life.",
        "Intangible cultural heritage protection needs community participation, for many traditional skills only can be continued by practicing in daily life."
      ],
      "answers": ["A", "B"],
      "explanation": "A、B 两项都准确表达“需要社区参与”和“只有通过日常持续实践才能延续”，被动与主动结构均自然。C 项 only can continue 语序错误，if practice 缺主语；D 项 only can be continued 语序不自然，by practicing 逻辑主语也不清楚。",
      "difficulty": "挑战"
    },
    {
      "id": "T6-04",
      "level": "CET-6",
      "category": "translation",
      "type": "single",
      "section": "译文辨析",
      "material": "人工智能的治理需要技术创新与伦理规范并重，确保技术发展服务于人类福祉。",
      "question": "Choose the best English translation.",
      "options": [
        "AI governance requires equal attention to technological innovation and ethical norms, ensuring that technological development serves human well-being.",
        "AI governance needs technological innovation and ethical norms pay equal attention, to ensure technology development serves human welfare.",
        "AI governance requires paying attention to technological innovation and ethical norms equally, and ensure technological development serves human well-being.",
        "AI governance needs to pay equal attention on technological innovation and ethical norms, ensuring technology development to serve human well-being."
      ],
      "answers": ["A"],
      "explanation": "A 项 equal attention to ... 搭配正确，ensuring that ... 作结果状语，serves human well-being 自然。B 项 needs ... pay equal attention 结构混乱；C 项 and ensure 与 requires paying 不平行；D 项 pay attention on 介词错误，ensure ... to serve 搭配不当。",
      "difficulty": "进阶"
    },
    {
      "id": "T6-05",
      "level": "CET-6",
      "category": "translation",
      "type": "single",
      "section": "译文辨析",
      "material": "建设书香社会，需要让阅读成为更多人日常生活的一部分，而不仅仅是学校里的任务。",
      "question": "Choose the best English translation.",
      "options": [
        "Building a reading society requires making reading part of more people's daily lives, rather than merely a task at school.",
        "To build a reading society needs to make reading a part of more people's daily life, not only a task in school.",
        "Building a reading society requires to make reading part of more people's daily lives instead of only school task.",
        "To build a reading society, reading needs to become part of more people's daily life, rather than only a school task."
      ],
      "answers": ["A"],
      "explanation": "A 项 requires making 搭配正确，part of more people's daily lives 与 rather than merely a task at school 对比清晰。B 项 To build ... needs 结构不自然；C 项 requires to make 应改为 requires making；D 项 reading needs to become 改变了原句主语，未体现“建设书香社会需要……”的逻辑。",
      "difficulty": "挑战"
    }
  ]
}
'''
