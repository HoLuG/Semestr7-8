import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:youtube_player_flutter/youtube_player_flutter.dart';



void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  static const String _title = 'Flutter Code Sample';

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      title: _title,
      home: MyStatefulWidget(),
    );
  }
}

class MyStatefulWidget extends StatefulWidget {
  const MyStatefulWidget({super.key});
  @override
  State<MyStatefulWidget> createState() => _MyStatefulWidgetState();
}




class _MyStatefulWidgetState extends State<MyStatefulWidget> {

late YoutubePlayerController _controller;


@override
void initState(){
    _controller = YoutubePlayerController(
        initialVideoId: 'iLnmTe5Q2Qw',
        flags: YoutubePlayerFlags(
            mute: false,
            autoPlay: true,
        ),
    );
    super.initState();
}



@override
Widget build(BuildContext context){
    return YoutubePlayer(
       controller: _controller,
       onReady: () {
          print('Player is ready.');
       },
    );
}




}



