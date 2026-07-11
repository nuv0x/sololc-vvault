import pyotp


def test_totp_generation():
    # 1. 生成一个标准的 Base32 密钥
    secret = "JBSWY3DPEHPK3PXP"

    # 2. 使用 pyotp 官方标准生成一个当前时间的验证码
    standard_otp = pyotp.TOTP(secret).now()

    # 3. 调用你自己编写的封装函数，检查输出是否一致
    # my_otp = totp.generate_code(secret)
    # assert my_otp == standard_otp

    # 临时断言示例：确保生成的验证码是 6 位数字
    assert len(standard_otp) == 6
    assert standard_otp.isdigit()
