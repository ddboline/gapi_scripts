"""Example of using hangups to send a chat message to a conversation."""

import asyncio

import hangups

from hangups_common import run_example

default_conversation = 'Ugw8V3Is1qGIG8M3Yg54AaABAQ'

default_conversation
@asyncio.coroutine
def send_message(client, args):
    request = hangups.hangouts_pb2.SendChatMessageRequest(
        request_header=client.get_request_header(),
        event_request_header=hangups.hangouts_pb2.EventRequestHeader(
            conversation_id=hangups.hangouts_pb2.ConversationId(
                id=default_conversation
            ),
            client_generated_id=client.get_client_generated_id(),
        ),
        message_content=hangups.hangouts_pb2.MessageContent(
            segment=[
                hangups.ChatMessageSegment(args.message_text).serialize()
            ],
        ),
    )
    yield from client.send_chat_message(request)


if __name__ == '__main__':
    run_example(send_message, '--message-text')