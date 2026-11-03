import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from unittest.mock import MagicMock
from mapper import Mapper
from twitch import TwitchChat, TwitchError


def resp(status, payload):
    r = MagicMock(); r.status_code = status; r.json.return_value = payload; r.text = str(payload)
    return r


def test_mapper_say_and_templates():
    tw = MagicMock()
    m = Mapper(tw, "chan", {"/twitch/brb": "BRB {0} min"})
    m.handle_osc_message("/twitch/say", "hello", 5)
    tw.send_message.assert_called_with("chan", "hello 5")
    m.handle_osc_message("/twitch/brb", 10)
    tw.send_message.assert_called_with("chan", "BRB 10 min")
    tw.reset_mock()
    m.handle_osc_message("/twitch/brb")      # missing arg
    m.handle_osc_message("/unknown", 1)
    tw.send_message.assert_not_called()


def test_send_message_flow():
    s = MagicMock()
    s.get.return_value = resp(200, {"client_id": "cid", "user_id": "42", "login": "bot",
                                    "scopes": ["user:write:chat"]})
    s.request.side_effect = [resp(200, {"data": [{"id": "99"}]}),
                             resp(200, {"data": [{"is_sent": True}]})]
    t = TwitchChat("tok", session=s)
    t.send_message("#Chan", "hi")
    post = s.request.call_args_list[1]
    assert post.args[:2] == ("POST", "https://api.twitch.tv/helix/chat/messages")
    assert post.kwargs["json"] == {"broadcaster_id": "99", "sender_id": "42", "message": "hi"}
    assert post.kwargs["headers"]["Client-Id"] == "cid"


def test_missing_scope_and_dropped():
    s = MagicMock()
    s.get.return_value = resp(200, {"client_id": "c", "user_id": "1", "scopes": []})
    try:
        TwitchChat("tok", session=s).validate(); assert False
    except TwitchError:
        pass
    s.get.return_value = resp(200, {"client_id": "c", "user_id": "1", "scopes": ["user:write:chat"]})
    s.request.side_effect = [resp(200, {"data": [{"id": "9"}]}),
                             resp(200, {"data": [{"is_sent": False, "drop_reason": {"code": "x"}}]})]
    try:
        TwitchChat("tok", session=s).send_message("c", "hi"); assert False
    except TwitchError:
        pass


def test_refresh_on_401():
    s = MagicMock()
    s.get.return_value = resp(200, {"client_id": "c", "user_id": "1", "scopes": ["user:write:chat"]})
    s.post.return_value = resp(200, {"access_token": "new", "refresh_token": "r2"})
    s.request.side_effect = [resp(401, {}), resp(200, {"data": [{"id": "9"}]}),
                             resp(200, {"data": [{"is_sent": True}]})]
    t = TwitchChat("old", "r", "c", "sec", session=s)
    t.send_message("chan", "hi")
    assert t.access_token == "new" and t.refresh_token == "r2"
