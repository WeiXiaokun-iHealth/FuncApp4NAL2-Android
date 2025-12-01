package com.funcapp4nal2

import android.graphics.Color
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

class LogAdapter(private val logs: MutableList<LogEntry>) : 
    RecyclerView.Adapter<LogAdapter.LogViewHolder>() {

    class LogViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val tvTimestamp: TextView = view.findViewById(R.id.tvTimestamp)
        val tvMessage: TextView = view.findViewById(R.id.tvMessage)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): LogViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_log, parent, false)
        return LogViewHolder(view)
    }

    override fun onBindViewHolder(holder: LogViewHolder, position: Int) {
        val log = logs[position]
        holder.tvTimestamp.text = log.timestamp
        holder.tvMessage.text = log.message
        
        // 根据日志类型设置颜色
        holder.tvMessage.setTextColor(when (log.type) {
            "ERROR" -> Color.parseColor("#FF3B30")
            "SUCCESS" -> Color.parseColor("#34C759")
            "INFO" -> Color.parseColor("#007AFF")
            else -> Color.parseColor("#333333")
        })
    }

    override fun getItemCount() = logs.size

    fun addLog(log: LogEntry) {
        logs.add(0, log)
        notifyItemInserted(0)
    }

    fun clearLogs() {
        val size = logs.size
        logs.clear()
        notifyItemRangeRemoved(0, size)
    }
}
