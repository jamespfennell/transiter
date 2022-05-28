// Package constants contains the canoncial string values for constants that are persisted in the database.
package constants

const (
	// System status
	Installing    = "INSTALLING"
	InstallFailed = "INSTALL_FAILED"
	Active        = "ACTIVE"
	Updating      = "UPDATING"
	UpdateFailed  = "UPDATE_FAILED"

	// Feed update status
	StatusRunning = "RUNNING"
	StatusSuccess = "SUCCESS"
	StatusFailure = "FAILURE"

	// Feed update result
	ResultUpdated           = "UPDATED"
	ResultNotNeeded         = "NOT_NEEDED"
	ResultParseError        = "PARSE_ERROR"
	ResultDownloadError     = "DOWNLOAD_ERROR"
	ResultInvalidParser     = "INVALID_PARSER"
	ResultInvalidFeedConfig = "INVALID_FEED_CONFIG"
	ResultEmptyFeed         = "EMPTY_FEED"
	ResultUpdateError       = "UPDATE_ERROR"
	ResultInternalError     = "INTERNAL_ERROR"
)
