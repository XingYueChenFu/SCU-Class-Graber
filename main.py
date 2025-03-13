from utils import BugFree, ClassGraber
import yaml

def main():
    config = yaml.safe_load(open('config.yaml', 'r', encoding='utf-8'))
    
    bugfree = BugFree(config)
    bugfree()
    
    classgraber = ClassGraber(config)
    
    classgraber.open_edge()
    classgraber.login()
    
    while True:
        classgraber.enter_course_select()
        classgraber.select_course()
        if classgraber.handle_result():
            break

if __name__ == '__main__':
    main()