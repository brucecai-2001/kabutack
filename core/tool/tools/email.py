import smtplib
from email.mime.text import MIMEText

from utils.config import agent_config
from core.tool.tool_utils import register_tool


@register_tool(func_name='email',
               func_desc="Email could be used to contact with user.",
               func_import="from core.tool.tools.email import email",
               func_args="""email_content (str): the content sent to user through email""",
               func_return="NoneType",
               func_example="email(email_content='Hi, How are you today?')")
def email(email_content: str = None, 
          react_params: dict = None):

    # This dictionary is used for ReAct agent, code agent does not need it
    if react_params is not None:
        email_content = react_params['email_content']

    # 邮箱的用户名和授权码
    email_user = agent_config.get('tools.email.agent_email')
    email_pass = agent_config.get('tools.email.agent_pass')
    
    # 发件人邮箱和收件人邮箱
    from_addr = email_user
    to_addr = agent_config.get('tools.email.user_email')

    # 邮件内容
    subject = 'Task'
    body = f'''<p> {email_content} </p>'''  # 定义邮件正文为html
    msg = MIMEText(body, 'html', 'utf-8')
    msg['from'] = from_addr
    msg['to'] = to_addr
    msg['subject'] = subject

    try:
        smtp = smtplib.SMTP()
        smtp.connect('smtp.163.com' )    # 链接服务器
        smtp.login(email_user, email_pass)     # 登录
        smtp.sendmail(from_addr, to_addr, msg.as_string())  # 发送
        smtp.quit()             # 关闭
        
        return "Email sent successfully"
        
    except Exception as e:
        raise Exception("Call Email failed: "+str(e))
