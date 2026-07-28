package com.example.kotlin_auth5_klicker_fb

import android.content.Context
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.BaseAdapter
import androidx.appcompat.widget.AppCompatTextView

class MusicListAdapter(
    val context: Context,
    val list: ArrayList<MusicStyle>
) : BaseAdapter() {
    
    override fun getCount(): Int {
        return list.size
    }

    override fun getItem(position: Int): Any {
        return list[position]
    }

    override fun getItemId(position: Int): Long {
        return position.toLong()
    }

    override fun getView(position: Int, convertView: View?, parent: ViewGroup?): View {
        val view: View = LayoutInflater.from(context).inflate(R.layout.row_layout, parent, false)
        val musicId = view.findViewById<AppCompatTextView>(R.id.music_id)
        val musicType = view.findViewById<AppCompatTextView>(R.id.music_type)
        val musicGenre = view.findViewById<AppCompatTextView>(R.id.music_genre)
        val musicUrl = view.findViewById<AppCompatTextView>(R.id.music_url)

        musicId.text = list[position].id.toString()
        musicType.text = list[position].musicType
        musicGenre.text = list[position].genre
        musicUrl.text = list[position].url

        return view
    }
}


