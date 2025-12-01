package com.ihealth.nal2.api.caller

data class LogEntry(
    val id: Long,
    val timestamp: String,
    val type: String,
    val message: String
)
