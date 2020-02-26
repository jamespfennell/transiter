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


@pytest.mark.parametrize(
    "custom_parser,feed_content,expected_explanation",
    [
        ["unknown_package:unknown_function", None, "INVALID_PARSER"],
        ["json:dump", None, "DOWNLOAD_ERROR"],
        ["json:dump", "", "EMPTY_FEED"],
        ["json:dump", "somethings", "PARSE_ERROR"],
        ["collections:OrderedDict", "somethings", "SYNC_ERROR"],
    ],
)
def test_invalid_parser(
    transiter_host,
    install_system,
    source_server,
    source_server_host_within_transiter,
    custom_parser,
    feed_content,
    expected_explanation,
):
    system_id = "test_invalid_parser__" + str(
        abs(hash((custom_parser, feed_content, expected_explanation)))
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

    feed_update = requests.post(
        transiter_host + "/systems/" + system_id + "/feeds/feed_1"  # /feed_1"
    ).json()

    assert feed_update["status"] == "FAILURE"
    assert feed_update["explanation"] == expected_explanation
