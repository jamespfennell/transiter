import time

import pytest
import requests

SYSTEM_CONFIG = """
name: Test System
feeds:
  feed_1:
    http:
      url: "{feed_url}"
    parser:
      {parser}
    required_for_install: false
"""


@pytest.mark.parametrize("sync", [True, False])
@pytest.mark.parametrize(
    "custom_parser,feed_content,expected_result",
    [
        ["unknown_package:unknown_function", None, "INVALID_PARSER"],
        ["json:dump", None, "DOWNLOAD_ERROR"],
        ["json:dump", "", "EMPTY_FEED"],
        ["json:dump", "somethings", "PARSE_ERROR"],
        ["collections:OrderedDict", "somethings", "PARSE_ERROR"],
    ],
)
def test_invalid_parser(
    transiter_host,
    install_system,
    source_server,
    source_server_host_within_transiter,
    sync,
    custom_parser,
    feed_content,
    expected_result,
):
    system_id = "test_invalid_parser__" + str(
        abs(hash((sync, custom_parser, feed_content, expected_result)))
    )
    if feed_content is not None:
        feed_url = source_server.create("", "/" + system_id + "/feed_1")
        source_server.put(feed_url, feed_content)
    else:
        feed_url = "not_used"
    system_config = SYSTEM_CONFIG.format(
        feed_url=source_server_host_within_transiter + "/" + feed_url,
        parser="custom: {}".format(custom_parser),
    )
    install_system(system_id, system_config)

    if sync:
        feed_update = requests.post(
            transiter_host + "/systems/" + system_id + "/feeds/feed_1?sync=true"
        ).json()
    else:
        feed_update = requests.post(
            transiter_host + "/systems/" + system_id + "/feeds/feed_1"
        ).json()
        for __ in range(20):
            feed_update = requests.get(
                transiter_host + "/systems/" + system_id + "/feeds/feed_1/updates"
            ).json()[0]
            if feed_update["status"] == "FAILURE":
                break
            time.sleep(0.05)

    assert feed_update["status"] == "FAILURE"
    assert feed_update["result"] == expected_result
