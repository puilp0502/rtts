window.jQuery = require('jquery');
window.$ = require('jquery');
require('./node_modules/materialize-css/dist/css/materialize.css');
require('./node_modules/materialize-css/dist/js/materialize.js');
require('./css/realtime.css');

const moment = require('moment');
io = require('socket.io-client');
socket = io();

const tmpl = require('./templates/tweet.njk');

jQuery(document).ready(function(){
    const dummyForm = $('#dummy-form');
    const stopBtn = $('#stop');
    const link_builder = function(href, text){
        return '&nbsp;<a target="_blank" href="'+href+'">'+text+'</a>&nbsp;'
    };
    const process_tweet = function(msg){
        let entities = msg.entities;
        if (entities !== undefined){
            for (let hashtag of entities.hashtags){
                let href = 'https://twitter.com/hashtag/'+hashtag.text;
                let display = '#'+hashtag.text;
                msg.text = msg.text.replace(display, link_builder(href, display));
            }
            for (let url of entities.urls){
                msg.text = msg.text.replace(url.url, link_builder(url.expanded_url, url.display_url));
            }
            for (let mention of entities.user_mentions){
                let href = 'https://twitter.com/'+mention.screen_name;
                let display = '@' + mention.screen_name;
                msg.text = msg.text.replace(display, link_builder(href, display));
            }
        }
        msg.time = moment(parseInt(msg.timestamp_ms)).format('HH:mm:ss.SSS');
        return msg;
    };
    dummyForm.submit(function(){
        let query = $('#query').val();
        console.log('Emitting message set query'+query);
        socket.emit('set query', query);
        $('title').html(query + ' - RTTS (Live)');
        stopBtn.removeClass('disabled');
        return false;
    });
    stopBtn.click(function(){
        socket.emit('stop query');
        stopBtn.addClass('disabled');
        $('title').html('Search - RTTS');
    });
    socket.on('tweet', function(msg){
        msg = JSON.parse(msg);
        msg = process_tweet(msg);
        if (msg.retweeted_status !== undefined){
            msg.retweeted_status = process_tweet(msg.retweeted_status);
        } else if (msg.quoted_status !== undefined){
            msg.quoted_status = process_tweet(msg.quoted_status);
        }
        let node = tmpl.render({'tweet': msg});
        $('#rtt').prepend(node);
    });
    socket.on('error', function(msg){
        $('#rtt').prepend('<div class="red darken-3 text-center">Error occured:'+msg+"</div>")
    })
});

