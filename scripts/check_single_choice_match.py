#!/usr/bin/env python3
"""
检查DeepSeek单选题答案是否与题目PDF一致
"""
import pdfplumber
import os
import re
import logging

logging.getLogger('pdfplumber').setLevel(logging.ERROR)

os.chdir('/Users/air/Downloads/GUIDE_AI_3/人工智能训练师_3级_sucai')

print("="*60)
print("检查DeepSeek单选题答案与题目PDF是否一致")
print("="*60)

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

# 解析DeepSeek答案
deepseek_answers = {}
pattern = r'(\d+)\.\s*([A-D])'
for match in re.finditer(pattern, deepseek_single_str):
    num = int(match.group(1))
    answer = match.group(2)
    deepseek_answers[num] = answer

print(f"DeepSeek单选题答案: {len(deepseek_answers)} 题")
print(f"题号范围: {min(deepseek_answers.keys())} - {max(deepseek_answers.keys())}")

# 提取题目PDF中的单选题
questions_pdf = '/Users/air/Downloads/GUIDE_AI_3/第3部分-人工智能训练师_3级_理论知识复习题.pdf'

print("\n提取题目PDF中的单选题...")
with pdfplumber.open(questions_pdf) as pdf:
    full_text = '\n'.join([page.extract_text() or '' for page in pdf.pages])

# 提取单选题部分
single_choice_section = re.search(r'二、单选题.*?(?=三、|四、|$)', full_text, re.DOTALL)
if single_choice_section:
    single_text = single_choice_section.group()
    # 提取所有单选题
    single_questions = re.findall(r'(\d+)\.\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*\d+\.|\n\s*[A-Z][\.．])', single_text)
    
    print(f"题目PDF中单选题: {len(single_questions)} 题")
    
    # 检查题号
    question_nums = []
    for num, q in single_questions:
        question_nums.append(int(num))
    
    if question_nums:
        print(f"题目题号范围: {min(question_nums)} - {max(question_nums)}")
        
        # 检查是否连续
        expected_nums = list(range(min(question_nums), max(question_nums) + 1))
        missing_nums = set(expected_nums) - set(question_nums)
        if missing_nums:
            print(f"缺失题号: {sorted(missing_nums)}")
        else:
            print("✅ 题号连续")
        
        # 检查DeepSeek答案与题目是否匹配
        deepseek_nums = set(deepseek_answers.keys())
        question_nums_set = set(question_nums)
        
        if deepseek_nums == question_nums_set:
            print("✅ DeepSeek答案与题目完全匹配")
        else:
            extra_in_deepseek = deepseek_nums - question_nums_set
            missing_in_deepseek = question_nums_set - deepseek_nums
            if extra_in_deepseek:
                print(f"DeepSeek多出的题号: {sorted(extra_in_deepseek)}")
            if missing_in_deepseek:
                print(f"DeepSeek缺少的题号: {sorted(missing_in_deepseek)}")
        
        # 显示前5题
        print("\n前5题示例:")
        for i, (num, q) in enumerate(single_questions[:5]):
            print(f"\n{num}. {q[:100]}")
            if int(num) in deepseek_answers:
                print(f"   DeepSeek答案: {deepseek_answers[int(num)]}")
else:
    print("❌ 未找到单选题部分")

print("\n" + "="*60)
print("检查完成")
print("="*60)