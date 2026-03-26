def test_send_sms_is_disabled():
    from services.twilioService import send_sms

    result = send_sms("+2348000000000", "hello")

    assert result is None
