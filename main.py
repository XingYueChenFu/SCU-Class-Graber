from utils import BugFree, ClassGraber
import yaml

def main():
    config = yaml.safe_load(open('config.yaml', 'r', encoding='utf-8'))
    
    bugfree = BugFree(config['bugfree'])
    bugfree()
    
    classgraber = ClassGraber(config)
    
    classgraber.open_edge() # 打开浏览器
    classgraber.login()     # 登录(可以处理验证码)
    classgraber.enter_course_select() # 进入选课页面
    
    while True:
        classgraber.select_course()       # 选课 (在有课余量时才选课，可以处理验证码)
        if classgraber.handle_result():   # 处理选课结果(True: 选课成功, False: 选课失败)
            break

if __name__ == '__main__':
    main()