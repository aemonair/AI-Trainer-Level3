#!/usr/bin/env python3
"""
生成最终Anki卡片（含DeepSeek答案+PDF官方答案对比）
- 标注DeepSeek答案
- 标注PDF官方答案
- 对比两者差异并标注
"""
import pdfplumber
import os
import re
import csv
import logging

logging.getLogger('pdfplumber').setLevel(logging.ERROR)

os.chdir('/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai')

print("="*60)
print("生成最终Anki卡片（DeepSeek答案 vs PDF官方答案对比）")
print("="*60)

# DeepSeek判断题答案
deepseek_judgment_str = """1√ 2× 3× 4× 5× 6× 7× 8× 9× 10×
11√ 12× 13× 14× 15√ 16√ 17√ 18√ 19√ 20√
21√ 22√ 23√ 24√ 25√ 26√ 27√ 28× 29× 30√
31× 32√ 33× 34√ 35√ 36√ 37× 38× 39√ 40√
41√ 42√ 43√ 44× 45× 46√ 47√ 48× 49√ 50√
51√ 52√ 53√ 54× 55× 56× 57× 58√ 59√ 60×
61× 62× 63√ 64√ 65√ 66× 67√ 68√ 69√ 70√
71× 72√ 73√ 74√ 75× 76√ 77√ 78× 79√ 80×
81√ 82√ 83√ 84× 85√ 86× 87√ 88√ 89× 90√
91√ 92√ 93× 94√ 95√ 96× 97× 98√ 99× 100√
101× 102√ 103√ 104√ 105× 106√ 107√ 108× 109√ 110√
111√ 112√ 113√ 114√ 115√ 116√ 117√ 118√ 119× 120√
121× 122√ 123× 124× 125√ 126√ 127√ 128× 129√ 130√
131× 132× 133× 134× 135√ 136× 137√ 138√ 139× 140√
141√ 142× 143√ 144√ 145√ 146√ 147√ 148× 149√ 150√
151√ 152√ 153√ 154√ 155× 156√ 157× 158× 159√ 160×
161√ 162√ 163× 164× 165√ 166√ 167√ 168× 169× 170×
171× 172√ 173√ 174× 175× 176× 177√ 178√ 179× 180√
181√ 182× 183√ 184√ 185√ 186× 187√ 188× 189√ 190√
191× 192√ 193× 194√ 195× 196√ 197√ 198× 199√ 200√
201√ 202× 203× 204√ 205√ 206× 207× 208× 209√ 210×
211√ 212× 213√ 214√ 215√ 216× 217× 218√ 219√ 220√
221× 222√ 223√ 224√ 225× 226√ 227√ 228× 229× 230√
231√ 232√ 233√ 234√ 235× 236× 237√ 238× 239√ 240√
241× 242√ 243√ 244√ 245× 246× 247× 248× 249× 250√
251√ 252√ 253√ 254√ 255× 256√ 257× 258× 259× 260√
261× 262√ 263× 264× 265× 266× 267√ 268× 269√ 270√
271√ 272√ 273× 274√ 275√ 276× 277√ 278√ 279× 280√
281√ 282× 283√ 284√ 285√ 286√ 287√ 288× 289× 290√
291× 292× 293√ 294√ 295× 296× 297√ 298× 299√ 300√"""

# 解析DeepSeek判断题答案
deepseek_judgment_answers = {}
pattern = r'(\d+)([√×])'
for match in re.finditer(pattern, deepseek_judgment_str):
    num = int(match.group(1))
    answer = match.group(2)
    deepseek_judgment_answers[num] = answer

print(f"DeepSeek判断题答案: {len(deepseek_judgment_answers)} 题")

# DeepSeek单选题答案
deepseek_single_str = """1. A  
2. B  
3. B  
4. C  
5. D  
6. D  
7. B  
8. D  
9. B  
10. D  
11. A  
12. C  
13. B  
14. B  
15. D  
16. D  
17. A  
18. A  
19. A  
20. A  
21. D  
22. A  
23. A  
24. D  
25. A  
26. A  
27. B  
28. B  
29. D  
30. D  
31. B  
32. D  
33. A  
34. C  
35. C  
36. D  
37. D  
38. D  
39. D  
40. C  
41. B  
42. A  
43. B  
44. D  
45. C  
46. A  
47. A  
48. D  
49. C  
50. A  
51. C  
52. D  
53. C  
54. A  
55. A  
56. A  
57. C  
58. A  
59. A  
60. B  
61. A  
62. D  
63. A  
64. B  
65. D  
66. A  
67. C  
68. B  
69. C  
70. D  
71. C  
72. C  
73. D  
74. C  
75. A  
76. A  
77. D  
78. A  
79. B  
80. A  
81. A  
82. C  
83. B  
84. A  
85. C  
86. A  
87. C  
88. A  
89. D  
90. D  
91. C  
92. D  
93. B  
94. A  
95. B  
96. A  
97. A  
98. C  
99. B  
100. A  
101. B  
102. B  
103. A  
104. D  
105. C  
106. A  
107. A  
108. D  
109. A  
110. A  
111. B  
112. C  
113. B  
114. A  
115. B  
116. B  
117. A  
118. A  
119. C  
120. B  
121. C  
122. D  
123. B  
124. B  
125. A  
126. A  
127. D  
128. A  
129. A  
130. B  
131. D  
132. B  
133. D  
134. A  
135. B  
136. B  
137. B  
138. A  
139. A  
140. A  
141. B  
142. C  
143. A  
144. B  
145. C  
146. A  
147. B  
148. C  
149. B  
150. C  
151. D  
152. D  
153. A  
154. C  
155. B  
156. A  
157. C  
158. A  
159. A  
160. A  
161. C  
162. B  
163. D  
164. C  
165. C  
166. C  
167. C  
168. B  
169. C  
170. B  
171. A  
172. B  
173. C  
174. A  
175. A  
176. A  
177. D  
178. B  
179. A  
180. A  
181. A  
182. C  
183. C  
184. B  
185. C  
186. B  
187. D  
188. D  
189. B  
190. B  
191. C  
192. A  
193. D  
194. A  
195. C  
196. B  
197. B  
198. C  
199. B  
200. A  
201. C  
202. C  
203. A  
204. A  
205. C  
206. D  
207. D  
208. B  
209. D  
210. C  
211. D  
212. A  
213. C  
214. A  
215. A  
216. A  
217. A  
218. A  
219. A  
220. B  
221. A  
222. D  
223. D  
224. B  
225. B  
226. A  
227. C  
228. B  
229. A  
230. A  
231. C  
232. C  
233. D  
234. B  
235. B  
236. A  
237. A  
238. C  
239. A  
240. B  
241. B  
242. A  
243. A  
244. B  
245. B  
246. A  
247. B  
248. B  
249. C  
250. D  
251. D  
252. A  
253. A  
254. A  
255. C  
256. C  
257. A  
258. B  
259. B  
260. B  
261. C  
262. C  
263. B  
264. A  
265. C  
266. B  
267. C  
268. A  
269. D  
270. C  
271. D  
272. A  
273. C  
274. C  
275. A  
276. C  
277. C  
278. A  
279. B  
280. B  
281. A  
282. C  
283. A  
284. C  
285. A  
286. A  
287. C  
288. B  
289. C  
290. A  
291. C  
292. A  
293. D  
294. A  
295. B  
296. C  
297. C  
298. C  
299. B  
300. B"""

# 解析DeepSeek单选题答案
deepseek_single_answers = {}
pattern = r'(\d+)\.\s*([A-D])'
for match in re.finditer(pattern, deepseek_single_str):
    num = int(match.group(1))
    answer = match.group(2)
    deepseek_single_answers[num] = answer

print(f"DeepSeek单选题答案: {len(deepseek_single_answers)} 题")

# PDF官方答案（从答案PDF中提取）
answers_pdf = '/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai/answers/人工智能训练师三级题库+答案（900题）.pdf'
pdf_judgment_answers = {}
pdf_single_answers = {}

print("\n提取PDF官方答案...")
with pdfplumber.open(answers_pdf) as pdf:
    full_text = '\n'.join([page.extract_text() or '' for page in pdf.pages])
    
    # 提取判断题答案
    judgment_pattern = r'(\d+)\.\s+[^\n]+?\s*答案[：:]\s*([√×])'
    for match in re.finditer(judgment_pattern, full_text):
        num = int(match.group(1))
        answer = match.group(2)
        pdf_judgment_answers[num] = answer
    
    # 提取单选题答案
    single_pattern = r'(\d+)\.\s+[^\n]+?\n\s*A\.[^\n]+\n\s*B\.[^\n]+\n\s*C\.[^\n]+\n\s*D\.[^\n]+\n\s*答案[：:]\s*([A-D])'
    for match in re.finditer(single_pattern, full_text):
        num = int(match.group(1))
        answer = match.group(2)
        pdf_single_answers[num] = answer

print(f"PDF官方判断题答案: {len(pdf_judgment_answers)} 题")
print(f"PDF官方单选题答案: {len(pdf_single_answers)} 题")

# 提取题目PDF
questions_pdf = '/Users/air/Downloads/GUIDE_AI_3/第3部分-人工智能训练师_3级_理论知识复习题.pdf'

print("\n提取题目PDF...")
with pdfplumber.open(questions_pdf) as pdf:
    full_text = '\n'.join([page.extract_text() or '' for page in pdf.pages])

# 分类提取题目
questions = {
    '判断题': [],
    '单选题': [],
    '多选题': []
}

judgment_pattern = r'[（(]\s*[）)]\s*\d+\.\s*([^\n]+)'
questions['判断题'] = re.findall(judgment_pattern, full_text)

single_choice_section = re.search(r'二、单选题.*?(?=三、|四、|$)', full_text, re.DOTALL)
if single_choice_section:
    single_text = single_choice_section.group()
    single_questions = re.findall(r'\d+\.\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*\d+\.|\n\s*[A-Z][\.．])', single_text)
    questions['单选题'] = single_questions

multiple_choice_section = re.search(r'三、多选题.*?(?=四、|五、|$)', full_text, re.DOTALL)
if multiple_choice_section:
    multiple_text = multiple_choice_section.group()
    multiple_questions = re.findall(r'\d+\.\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*\d+\.|\n\s*[A-Z][\.．])', multiple_text)
    questions['多选题'] = multiple_questions

# 统计
print("\n" + "="*60)
print("题目数量统计")
print("="*60)
total = 0
for qtype, qlist in questions.items():
    count = len(qlist)
    total += count
    print(f"{qtype}: {count} 题")
print(f"总计: {total} 题")

# 生成Anki卡片
print("\n" + "="*60)
print("生成Anki卡片...")
print("="*60)

os.makedirs('anki_cards', exist_ok=True)

# 判断题
if questions['判断题']:
    with open('anki_cards/理论知识_判断题.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['正面', '背面'])
        for i, q in enumerate(questions['判断题']):
            front = f"【判断题】{q}"
            
            question_num = i + 1
            deepseek_answer = deepseek_judgment_answers.get(question_num)
            pdf_answer = pdf_judgment_answers.get(question_num)
            
            back_parts = []
            
            if deepseek_answer:
                back_parts.append(f"【DeepSeek答案】{deepseek_answer}")
            
            if pdf_answer:
                back_parts.append(f"【PDF官方答案】{pdf_answer}")
            
            if deepseek_answer and pdf_answer:
                if deepseek_answer == pdf_answer:
                    back_parts.append("✅ 两者答案一致")
                else:
                    back_parts.append("⚠️ 答案不一致，请确认！")
            elif deepseek_answer and not pdf_answer:
                back_parts.append("⚠️ PDF答案缺失")
            elif pdf_answer and not deepseek_answer:
                back_parts.append("⚠️ DeepSeek答案缺失")
            
            if not deepseek_answer and not pdf_answer:
                back_parts.append("⚠️ 暂无答案，请人工确认")
            
            back_parts.append(f"\n【题目】\n{q}")
            back = '\n\n'.join(back_parts)
            
            writer.writerow([front, back])
    
    print(f"✅ 判断题: {len(questions['判断题'])}题 → anki_cards/理论知识_判断题.csv")

# 单选题
if questions['单选题']:
    with open('anki_cards/理论知识_单选题.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['正面', '背面'])
        for i, q in enumerate(questions['单选题']):
            front = f"【单选题】{q}"
            
            question_num = i + 1
            deepseek_answer = deepseek_single_answers.get(question_num)
            pdf_answer = pdf_single_answers.get(question_num)
            
            back_parts = []
            
            if deepseek_answer:
                back_parts.append(f"【DeepSeek答案】{deepseek_answer}")
            
            if pdf_answer:
                back_parts.append(f"【PDF官方答案】{pdf_answer}")
            
            if deepseek_answer and pdf_answer:
                if deepseek_answer == pdf_answer:
                    back_parts.append("✅ 两者答案一致")
                else:
                    back_parts.append("⚠️ 答案不一致，请重点复习！")
            elif deepseek_answer and not pdf_answer:
                back_parts.append("⚠️ PDF答案缺失，此为AI预测答案")
            elif pdf_answer and not deepseek_answer:
                back_parts.append("⚠️ DeepSeek答案缺失")
            
            if not deepseek_answer and not pdf_answer:
                back_parts.append("⚠️ 暂无答案，请人工确认")
            
            back_parts.append(f"\n【题目】\n{q}")
            back = '\n\n'.join(back_parts)
            
            writer.writerow([front, back])
    
    print(f"✅ 单选题: {len(questions['单选题'])}题 → anki_cards/理论知识_单选题.csv")

# 多选题
if questions['多选题']:
    with open('anki_cards/理论知识_多选题.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['正面', '背面'])
        for i, q in enumerate(questions['多选题']):
            front = f"【多选题】{q}"
            back = f"【题目】\n{q}\n\n⚠️ 答案待补充（PDF中为颜色标记）"
            writer.writerow([front, back])
    
    print(f"✅ 多选题: {len(questions['多选题'])}题 → anki_cards/理论知识_多选题.csv")

# 合并版
with open('anki_cards/理论知识_全部题目.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow(['正面', '背面'])
    for qtype, qlist in questions.items():
        for i, q in enumerate(qlist):
            front = f"【{qtype}】{q}"
            
            if qtype == '判断题':
                question_num = i + 1
                deepseek_answer = deepseek_judgment_answers.get(question_num)
                pdf_answer = pdf_judgment_answers.get(question_num)
            elif qtype == '单选题':
                question_num = i + 1
                deepseek_answer = deepseek_single_answers.get(question_num)
                pdf_answer = pdf_single_answers.get(question_num)
            else:
                deepseek_answer = None
                pdf_answer = None
            
            back_parts = []
            if deepseek_answer:
                back_parts.append(f"【DeepSeek答案】{deepseek_answer}")
            if pdf_answer:
                back_parts.append(f"【PDF官方答案】{pdf_answer}")
            
            if deepseek_answer and pdf_answer:
                if deepseek_answer == pdf_answer:
                    back_parts.append("✅ 两者答案一致")
                else:
                    back_parts.append("⚠️ 答案不一致，请重点复习！")
            elif deepseek_answer and not pdf_answer:
                if qtype == '单选题':
                    back_parts.append("⚠️ PDF答案缺失，此为AI预测答案")
                else:
                    back_parts.append("⚠️ PDF答案缺失")
            elif pdf_answer and not deepseek_answer:
                back_parts.append("⚠️ DeepSeek答案缺失")
            
            if not deepseek_answer and not pdf_answer:
                if qtype == '判断题':
                    back_parts.append("⚠️ 暂无答案，请人工确认")
                else:
                    back_parts.append("⚠️ 答案待补充（PDF中为颜色标记）")
            
            back_parts.append(f"\n【题目】\n{q}")
            back = '\n\n'.join(back_parts)
            
            writer.writerow([front, back])

print(f"\n✅ 合并版: {total}题 → anki_cards/理论知识_全部题目.csv")

# 统计答案差异
judgment_same = 0
judgment_diff = 0
for i in range(1, 301):
    ds = deepseek_judgment_answers.get(i)
    pdf = pdf_judgment_answers.get(i)
    if ds and pdf:
        if ds == pdf:
            judgment_same += 1
        else:
            judgment_diff += 1

single_same = 0
single_diff = 0
for i in range(1, 301):
    ds = deepseek_single_answers.get(i)
    pdf = pdf_single_answers.get(i)
    if ds and pdf:
        if ds == pdf:
            single_same += 1
        else:
            single_diff += 1

# 统计
print("\n" + "="*60)
print("答案统计")
print("="*60)
print(f"判断题 - DeepSeek答案: {len(deepseek_judgment_answers)}题")
print(f"判断题 - PDF官方答案: {len(pdf_judgment_answers)}题")
print(f"判断题 - 答案一致: {judgment_same}题")
print(f"判断题 - 答案差异: {judgment_diff}题")
print(f"\n单选题 - DeepSeek答案: {len(deepseek_single_answers)}题")
print(f"单选题 - PDF官方答案: {len(pdf_single_answers)}题")
print(f"单选题 - 答案一致: {single_same}题")
print(f"单选题 - 答案差异: {single_diff}题")
print(f"\n多选题 - 答案待补充")

print("\n" + "="*60)
print("✅ 完成！")
print("="*60)