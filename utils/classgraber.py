from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException

from PIL import Image, ImageEnhance
from io import BytesIO
import base64

import time
import ddddocr
# from utils import BugFree

class ClassGraber:
    def __init__(self, config):
        self.config = config
        self.course_id_predix = config['course_id'].split('_')[0]  # 课程 ID 前缀
        
        self.loading_sleep_time = config['loading_sleep_time']
        self.render_sleep_time = config['render_sleep_time']
        self.jumping_wait_time = config['jumping_wait_time']
        
        # self.bugfree = BugFree(config)
        
        self.ocr = ddddocr.DdddOcr(show_ad=False) # 初始化识别器
        
    # 创建edge实例
    def open_edge(self):
        self.edge_service = EdgeService(executable_path=self.config['driver_path']) # 创建EdgeService实例
        self.driver = webdriver.Edge(service=self.edge_service) # 创建Edge浏览器实例
        
    # 登录
    def login(self):
        self._open_login_url()
        self._jump_to_unified_login()
        self._input_login_info()
        self._confirm_login()
        
    # 进入选课页面
    def enter_course_select(self):
        self._expand_sidebar()
        self._click_course_management()
        self._click_course_select()
        self._check_selectable()
    
    # 选课
    def select_course(self, course_id=None):
        if course_id:
            self.config['course_id'] = course_id
            self.course_id_predix = course_id.split('_')[0]
            
        self._click_free_course()
        self._switch_to_free_course_iframe()
        self._input_course_id()
        
        while True: # 循环查询直到有结果
            self._click_query_button()
            if self._check_has_course():
                if self._click_choose_course():
                    break
            time.sleep(self.config['query_interval']) # 等待 query_interval 秒再次查询
            
        self._input_course_captcha()
        self._click_submit_button()
        
    # 处理选课结果
    def handle_result(self):
        if self._check_result():
            return True
        else:
            print(f'\033[1;33m[warning]\033[0m 选课失败，将返回选课页面，重新选课')
            self._return_to_course_page()
            return False

    # //=======================================================//
    # //                        辅助函数                        //
    # //=======================================================//
    
    # ===== "登录" 辅助函数 =====
    # 打开登录网址
    def _open_login_url(self):
        self.driver.get(self.config['login_url'])
        print(f'\033[1;34m[info]\033[0m 打开登录网址: {self.config["login_url"]}，将等待 {self.loading_sleep_time} 秒，以便加载')
        time.sleep(self.loading_sleep_time)
    
    # 跳转到统一登录页面
    def _jump_to_unified_login(self):
        try:
            link = WebDriverWait(self.driver, self.jumping_wait_time).until( # 使用 XPATH 定位
                EC.presence_of_element_located((By.XPATH, '//a[@title="跳转统一认证"]'))
            )
            link.click()
            print(f'\033[1;32m[info]\033[0m 已点击 "跳转统一认证" 链接！')
        except Exception as e:
            print(f'\033[1;31m[Error]\033[0m 超过{self.jumping_wait_time}秒，等待 "跳转统一认证" 链接加载失败：\n{e}')
            raise e
    
    # 输入登录信息
    def _input_login_info(self):
        username_input = self.driver.find_element(By.XPATH, '//input[@placeholder="请输入学(工)号"]') # 找到用户名输入框
        password_input = self.driver.find_element(By.XPATH, '//input[@placeholder="请输入密码"]')     # 找到密码输入框
        captcha_input = self.driver.find_element(By.XPATH, '//input[@placeholder="请输入验证码"]')    # 找到验证码输入框
        captcha_img = self.driver.find_element(By.CLASS_NAME, 'captcha-img')                         # 找到验证码图片

        # 识别验证码
        captcha_src = captcha_img.get_attribute('src')
        captcha_base64 = captcha_src.split(',')[1] # 去掉 Base64 数据的前缀（如 "data:image/png;base64,"）
        captcha_image = Image.open(BytesIO(base64.b64decode(captcha_base64))) # 解码 Base64 数据
        check_code = self.ocr.classification(captcha_image) # 识别验证码
        print(f'\033[1;32m[info]\033[0m 识别验证码为：{check_code}')

        username_input.send_keys(self.config['username'])
        password_input.send_keys(self.config['password'])
        captcha_input.send_keys(check_code)
        print(f'\033[1;32m[info]\033[0m 已填写用户名、密码和验证码！')

        login_button = self.driver.find_element(By.CSS_SELECTOR, 'button.login-btn')
        login_button.click()
        print(f'\033[1;32m[info]\033[0m 已点击登录按钮！')
        
    # 确认登录是否成功
    def _confirm_login(self):
        try:
            WebDriverWait(self.driver, self.jumping_wait_time).until(EC.title_contains("URP高校教学管理与服务平台")) # "URP高校教学管理与服务平台（学生）"
            print(f'\033[1;34m[info]\033[0m 跳转成功，当前页面标题：{self.driver.title}')
        except Exception as e:
            print(f'\033[1;31m[Error]\033[0m 超过{self.jumping_wait_time}秒，等待跳转后的页面加载失败：\n{e}')
            raise e
    
    
    # ===== "进入选课页面" 辅助函数 =====
    # 展开侧边伸缩栏
    def _expand_sidebar(self):
        try:
            menu_toggler_button = self.driver.find_element(By.ID, 'menu-toggler')
            # 检查按钮是否可点击
            if menu_toggler_button.is_enabled() and menu_toggler_button.is_displayed():
                print(f'\033[1;34m[info]\033[0m "侧边栏伸缩按钮"可点击')
                menu_toggler_button.click()
                print(f'\033[1;34m[info]\033[0m 已点击"侧边栏伸缩按钮"，将等待{self.render_sleep_time}s，以便渲染网页内容')
                time.sleep(self.render_sleep_time)
            else:
                print(f'\033[1;33m[warning]\033[0m "侧边栏伸缩按钮"不可点击或被隐藏')
        except Exception as e:
            print(f'\033[1;31m[info]\033[0m 未找到"侧边栏伸缩按钮"或操作失败：\n{e}')
            raise e
    
    # 点击"选课管理"的界面
    def _click_course_management(self):
        try:
            course_management_link = self.driver.find_element(By.XPATH, '//span[contains(text(), "选课管理")]/parent::a')
            
            # 检查 <a> 标签是否可点击
            if course_management_link.is_enabled() and course_management_link.is_displayed():
                print(f'\033[1;34m[info]\033[0m "选课管理"链接可点击')
                course_management_link.click()
                print(f'\033[1;34m[info]\033[0m 已点击"选课管理"链接，将等待{self.render_sleep_time}s，以便渲染网页内容')
                time.sleep(self.render_sleep_time)
            else:
                print(f'\033[1;33m[warning]\033[0m "选课管理"链接不可点击或被隐藏')
        except Exception as e:
            print(f'\033[1;31m[Error]\033[0m 未找到"选课管理"链接或操作失败：\n{e}')
            raise e
    
    # 点击"选课"的界面
    def _click_course_select(self):
        try:
            course_select_link = self.driver.find_element(By.XPATH, '//a[contains(@href, "/student/courseSelect/courseSelect/index")]')
            
            # 检查链接是否可点击
            if course_select_link.is_enabled() and course_select_link.is_displayed():
                print(f'\033[1;34m[info]\033[0m "选课"链接可点击')
                course_select_link.click()
                print(f'\033[1;34m[info]\033[0m 已点击"选课"链接，将等待{self.loading_sleep_time}s，以便渲染网页内容')
                time.sleep(self.loading_sleep_time)
            else:
                print(f'\033[1;33m[warning]\033[0m "选课"链接不可点击或被隐藏')
        except Exception as e:
            print(f'\033[1;31m[Error]\033[0m 未找到"选课"链接或操作失败：\n')
            raise e
    
    # 查看是否可以选课
    def _check_selectable(self):
        try:
            # 查找 class 为 "alert alert-block alert-danger" 的 <div> 标签
            alert_div = self.driver.find_element(By.CLASS_NAME, 'alert.alert-block.alert-danger')
            print(f'\033[1;34m[info]\033[0m 找到提示信息框')

            # 检查 <div> 的内容是否包含 "对不起，当前为非选课阶段！"
            if "对不起，当前为非选课阶段！" in alert_div.text:
                print(f'\033[1;34m[info]\033[0m 提示信息内容：\033[31m{alert_div.text.strip()}\033[0m')

                # 查找 <div> 中的关闭按钮
                close_button = alert_div.find_element(By.XPATH, './/button[@type="button" and contains(@class, "close")]')
                
                # 检查按钮是否可点击
                if close_button.is_enabled() and close_button.is_displayed():
                    print(f'\033[1;34m[info]\033[0m 该提示信息有 可见并可点击的 关闭按钮')
                    # 抛出异常，内容为提示信息
                    e = alert_div.text.strip()
                    raise Exception(f"\033[1;31m{e}\033[0m \033[33m并不是脚本出错了！\033[0m")
                else:
                    print(f'\033[1;33m[warning]\033[0m 关闭按钮不可点击或被隐藏')
            else:
                print(f'\033[1;34m[info]\033[0m 提示信息框内容不匹配')
        except NoSuchElementException:
            print(f'\033[1;32m[Success]\033[0m 成功进入选课页面（未找到警告提示信息框）')
        except ElementNotInteractableException:
            print(f'\033[1;33m[warning]\033[0m 关闭按钮不可交互')
            raise e
        except Exception as e:
            print(f'\033[1;31m[Error]\033[0m 发生异常：\n{e}')
            raise e # 重新抛出异常

    # ===== "选课" 辅助函数 =====
    # 点击"自由选课"的界面
    def _click_free_course(self):
            # 查找 title 为 "自由选课" 的 <li> 标签并点击
        try:
            # 使用 XPath 定位
            free_course_li = self.driver.find_element(By.XPATH, '//li[@title="自由选课"]')
            
            # 检查是否可点击
            if free_course_li.is_enabled() and free_course_li.is_displayed():
                print(f'\033[1;34m[info]\033[0m 找到 "自由选课" 标签，准备点击')
                free_course_li.click()
                print(f'\033[1;34m[info]\033[0m 已点击 "自由选课" 标签')
            # else:
            #     print(f'\033[1;33m[warning]\033[0m "自由选课" 标签不可点击或被隐藏')
        except Exception as e:
            print(f'\033[1;31m[Error]\033[0m 未找到 "自由选课" 标签或点击失败：\n{e}')# 查找 title 为 "自由选课" 的 <li> 标签并点击

    # 切换到"自由选课"的iframe
    def _switch_to_free_course_iframe(self):
        try:
            # 使用 iframe 的 id 或 name 切换到 iframe
            iframe = self.driver.find_element(By.ID, 'ifra')
            self.driver.switch_to.frame(iframe)
            print(f'\033[1;34m[info]\033[0m 已切换到 iframe')
        except Exception as e:
            print(f'\033[1;31m[Error]\033[0m 切换到 iframe 失败：\n{e}')
            exit()
            
    # 输入课程号
    def _input_course_id(self):
        # 查找包含 "课程号" 的 div，并定位其下一个 div 中的输入框
        try:
            # 查找包含 "课程号" 的 div
            course_label_div = self.driver.find_element(By.XPATH, '//div[contains(text(), "课程号")]')
            print(f'\033[1;34m[info]\033[0m 找到包含 "课程号" 的 div')

            # 定位下一个 div 中的输入框
            course_input = course_label_div.find_element(By.XPATH, './following-sibling::div//input[@type="text"]')
            
            # 检查输入框是否可交互
            if course_input.is_enabled() and course_input.is_displayed():
                print(f'\033[1;34m[info]\033[0m 找到课程输入框，准备输入课程 ID')
                course_input.clear()  # 清空输入框（可选）
                course_input.send_keys(self.course_id_predix)  # 输入课程 ID 的前缀
                print(f'\033[1;34m[info]\033[0m 已输入课程 ID 的前缀: {self.course_id_predix}')
            else:
                print(f'\033[1;33m[warning]\033[0m 课程输入框不可交互或被隐藏')
        except Exception as e:
            print(f'\033[1;31m[Error]\033[0m 未找到输入框或输入失败：\n{e}')
    
    # 点击查询按钮
    def _click_query_button(self):
    # 查找 id 为 "queryButton" 的按钮并点击
        try:
            # 使用 ID 定位按钮
            query_button = self.driver.find_element(By.ID, 'queryButton')
            
            # 检查按钮是否可点击
            if query_button.is_enabled() and query_button.is_displayed():
                print(f'\033[1;34m[info]\033[0m 找到查询按钮，准备点击')
                query_button.click()
                print(f'\033[1;34m[info]\033[0m 已点击查询按钮')
            else:
                print(f'\033[1;33m[warning]\033[0m 查询按钮不可点击或被隐藏')
        except Exception as e:
            print(f'\033[1;31m[Error]\033[0m 未找到查询按钮或点击失败：\n{e}')
    
    # 查看是否有课余量
    def _check_has_course(self):
        try: # 查找内容包含 "未查询到记录！" 的 <td> 标签
            no_record_td = self.driver.find_element(By.XPATH, '//td[contains(text(), "未查询到记录！")]')
            print(f'\033[1;34m[info]\033[0m 找到提示信息：{no_record_td.text.strip()}')
            return False
        except NoSuchElementException:
            print(f'\033[1;34m[info]\033[0m 未找到 "未查询到记录！" 的提示信息，可能有课余量')
            return True
        except Exception as e:
            print(f'\033[1;31m[Error]\033[0m 查找提示信息失败：\n{e}')
            
    # 点击选课按钮
    def _click_choose_course(self):
        # 查找包含 config['course_id'] 的 <td> 标签
        try:
            time.sleep(0.1) # 等待标签加载出来
            # 使用 XPath 定位包含 config['course_id'] 的 <td> 标签
            course_td = self.driver.find_element(By.XPATH, f'//td[contains(text(), "{self.config["course_id"]}")]')
            print(f'\033[1;34m[info]\033[0m 找到包含课程 ID {self.config["course_id"]} 的 <td> 标签')
            # 找到其父标签 <tr>
            course_tr = course_td.find_element(By.XPATH, './parent::tr')
            print(f'\033[1;34m[info]\033[0m 找到父标签 <tr>')
            # 找到 <tr> 下的第一个 <td> 标签
            first_td = course_tr.find_element(By.XPATH, './/td[1]')
            print(f'\033[1;34m[info]\033[0m 找到第一个 <td> 标签')

            # 找到 <td> 下的 <label>  标签并点击
            label_checkbox = first_td.find_element(By.XPATH, './/label')
            if label_checkbox.is_enabled() and label_checkbox.is_displayed():
                print(f'\033[1;34m[info]\033[0m 找到复选框，准备点击')
                label_checkbox.click()
                print(f'\033[1;34m[info]\033[0m 已点击复选框')
                # 切换回默认内容（主页面） # 准备点击提交
                self.driver.switch_to.default_content()
                print(f'\033[1;34m[info]\033[0m 已切换回主页面')
                return True
            else:
                print(f'\033[1;33m[warning]\033[0m 复选框不可点击或被隐藏')
        except NoSuchElementException:
            print(f'\033[1;34m[info]\033[0m 未找到包含课程 ID {self.config["course_id"]} 的 <td> 标签')
            return False
        except Exception as e:
            print(f'\033[1;31m[Error]\033[0m 操作失败：{e}')
            
    # 输入选课验证码 
    def _input_course_captcha(self, max_try=3): # 最大尝试次数
        try:
            # 最多尝试3次识别验证码
            for i in range(max_try):
                # 查找验证码图片
                captcha_img_element = self.driver.find_element(By.XPATH, '//div[@id="yzm_area"]//img')
                
                # 截取验证码图片
                captcha_screenshot = captcha_img_element.screenshot_as_png
                print(f'\033[1;34m[info]\033[0m 已截取验证码图片')

                # 将截图转换为 PIL 图像
                captcha_image = Image.open(BytesIO(captcha_screenshot))

                # 增强图片对比度
                enhancer = ImageEnhance.Contrast(captcha_image)
                captcha_image = enhancer.enhance(2.0)  # 增强对比度，因子为 2.0
                print(f'\033[1;34m[info]\033[0m 已增强验证码图片对比度')
                
                # 识别验证码
                check_code = self.ocr.classification(captcha_image)
                print(f'\033[1;34m[info]\033[0m 验证码识别结果：{check_code}')
                if len(check_code) == 4:
                    break
                else:
                    print(f'\033[1;33m[warning]\033[0m 识别结果不是4位数，将重新识别')
                captcha_img_element.click()  # 点击验证码图片，刷新验证码
                time.sleep(self.config['render_sleep_time']) # 等待验证码刷新

            # 输入验证码
            submit_code_input = self.driver.find_element(By.ID, 'submitCode')
            submit_code_input.clear()  # 清空输入框
            submit_code_input.send_keys(check_code)  # 输入验证码
            print(f'\033[1;34m[info]\033[0m 已输入验证码：{check_code}')
        except NoSuchElementException:
            print(f'\033[1;31m[Error]\033[0m 未找到验证码图片或输入框')
        except Exception as e:
            print(f'\033[1;31m[Error]\033[0m 操作失败：{e}')
    
    # 点击提交按钮
    def _click_submit_button(self):
        # 查找 id 为 "submitButton" 的按钮并点击
        try:
            # 使用 ID 定位按钮
            submit_button = self.driver.find_element(By.ID, 'submitButton')
            
            # 检查按钮是否可点击
            if submit_button.is_enabled() and submit_button.is_displayed():
                print(f'\033[1;34m[info]\033[0m 找到提交按钮，准备点击')
                submit_button.click()
                print(f'\033[1;34m[info]\033[0m 已点击提交按钮')
            else:
                print(f'\033[1;33m[warning]\033[0m 提交按钮不可点击或被隐藏')
        except Exception as e:
            print(f'\033[1;31m[Error]\033[0m 未找到提交按钮或点击失败：{e}')
    
    # ===== "处理选课结果" 辅助函数 =====
    # 检查选课结果
    def _check_result(self):
        try:
            fail_to_grab_class = self.driver.find_element(By.XPATH, '//span[contains(text(), "你选择的课程没有课余量！")]')
            print(f'\033[1;34m[info]\033[0m {fail_to_grab_class.text}')
            return False
        except NoSuchElementException:
            print(f'\033[1;32m[Succuss]\033[0m 如果前面没有error 选课成功！')
            return True
        except Exception as e:
            print(f'\033[1;31m[Error]\033[0m 选课失败：{e}')
    
    # 返回选课界面
    def _return_to_course_page(self):
        # 查找 title 为 "返回" 的 <button> 标签并点击
        try:
            # 使用 XPath 定位
            back_button = self.driver.find_element(By.XPATH, '//button[@title="返回"]')
            
            # 检查按钮是否可点击
            if back_button.is_enabled() and back_button.is_displayed():
                print(f'\033[1;34m[info]\033[0m 找到 "返回" 按钮，准备点击')
                back_button.click()
                print(f'\033[1;34m[info]\033[0m 已点击 "返回" 按钮')
            else:
                print(f'\033[1;33m[warning]\033[0m "返回" 按钮不可点击或被隐藏')
        except NoSuchElementException:
            print(f'\033[1;34m[info]\033[0m 未找到 "返回" 按钮')
        except Exception as e:
            print(f'\033[1;31m[Error]\033[0m 点击 "返回" 按钮失败：{e}')
            
        