(($) ->
  'use strict'

  window.WebSocket = window.MozWebSocket if not window.WebSocket and window.MozWebSocket

  $.support.websocket = window.WebSocket and true or false

  websocket = $.websocket = (url, options) ->
    options = $.extend true, {}, websocket.defaults, options
    ws = new WebSocket(url)
    $(ws).bind('open', options.open)
         .bind('close', options.close)
         .bind('error', options.error)
         .bind('message', options.message)
    return ws

  websocket.defaults =
    open: ->
      return
    close: ->
      return
    error: ->
      return
    message: (event) ->
      return

) jQuery

