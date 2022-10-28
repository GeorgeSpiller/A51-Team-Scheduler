class bc:
    GREY        = '\033[90m'
    DARK_BLUE   = '\033[34m'
    CYAN        = '\033[96m'
    PURPLE      = '\033[95m'
    GREEN       = '\033[92m'
    WARNING     = '\033[93m'
    ERROR       = '\033[91m'
    ENDC        = '\033[0m'
    BOLD        = '\033[1m'


if __name__ == '__main__':
    print(f''' 
    {bc.GREY} GREY {bc.ENDC}
    {bc.DARK_BLUE} DARK_BLUE {bc.ENDC}
    {bc.CYAN} CYAN {bc.ENDC}
    {bc.PURPLE} PURPLE {bc.ENDC}
    {bc.GREEN} GREEN {bc.ENDC}
    {bc.WARNING} WARNING {bc.ENDC}
    {bc.ERROR} ERROR {bc.ENDC}    
    {bc.BOLD} BOLD {bc.ENDC}
    ''')