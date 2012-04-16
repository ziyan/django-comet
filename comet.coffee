(($, exports) ->
  'use strict'

  cookie = 0

  process_data = (data) ->
    return if not data
    cookie = data.cookie
    debug.info 'jl.comet cookie: ' + cookie
    events = data.events or []
    for event in events
      comet_event = $.Event 'comet:event',
        event: event
      debug.info 'comet:event(' + JSON.stringify(event) + ')'
      $(window.document.body).trigger comet_event

  ajax = null

  start_ajax = ->
    return if ajax or not status.token

    url = location.protocol + '//'
    url += location.host
    url += '/comet/ajax/'

    ajax = $.ajax
      type: 'POST'
      url: url
      dataType: 'json'
      data:
        token: status.token
        cookie: cookie

    ajax.done (data) ->
      ajax = null
      process_data data

      # restart request to poll the next events
      setTimeout start_ajax, 3000

    ajax.error (xhr, txt_status) ->
      ajax = null
      return if txt_status is 'abort'
      debug.error 'comet ajax polling error: ' + txt_status
      setTimeout start_ajax, 3000

  stop_ajax = ->
    return if not ajax
    ajax.abort()
    ajax = null
    cookie = 0

  websocket = null
  websocket_retry = 0

  start_websocket = ->
    return if websocket or not status.token

    qs = $.param
      token: status.token
      cookie: cookie
    url = location.protocol is 'https:' and 'wss://' or 'ws://'
    url += location.host
    url += '/comet/websocket/?'
    url += qs
    websocket = $.websocket url,
      message: (event) ->
        data = event.originalEvent.data
        debug.info 'comet websocket received message: ' + data
        process_data JSON.parse(data)
      open: ->
        debug.info 'comet websocket opened connection to: ' + url
        websocket_retry = 0
      close: ->
        websocket = null
        debug.info 'comet websocket connection closed: ' + url
        return if websocket_retry > 3
        websocket_retry++
        setTimeout start_websocket, 3000

  stop_websocket = ->
    return if not websocket
    $(websocket).unbind('close')
    websocket.close()
    websocket = null
    cookie = 0

  $ ->

    $(window.document.body).live 'status:change', (event) ->
      if $.support.websocket
        stop_websocket()
        start_websocket()
      else
        stop_ajax()
        start_ajax()

)(jQuery, window)

