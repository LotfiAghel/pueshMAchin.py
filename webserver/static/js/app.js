var app = angular.module('app', ['ngWebSocket']);

app.factory('ws', function($websocket) {
  // Open a WebSocket connection
  var dataStream = $websocket("ws://" + location.host + "/ws", null, {
    reconnectIfNotNormalClose: true
  });

  var methods = {
    onMessage: function(cb) {
      dataStream.onMessage(cb)
    },
    onClose: function(cb) {
      dataStream.onClose(cb)
    },
    get: function(data) {
      dataStream.send(JSON.stringify(data));
    }
  };

  return methods;
})

app.controller('app_controller', function($scope, ws) {
  $scope.no_connection = true;

  ws.onMessage(function(message) {
    $scope.no_connection = false;
    message = JSON.parse(message.data).v1
    switch (message.type) {
      case 'architecture':
        $scope.nodes = message.payload;
        $scope.scripts = message.scripts;
        // $scope.nodes[2].selected = true;
        // $scope.nodes[3].selected = true;
        // $scope.nodes[4].selected = true;
        // $scope.nodes[5].selected = true;
        // $scope.nodes[6].selected = true;
        // $scope.nodes[7].selected = true;
        break;
      case 'status_update':
        $scope.update_node_status(message.nodes);
        $scope.update_system_status(message.system);
        $scope.errors = message.errors;
        break;
      case 'response':
        console.log(message);
        break;
      default:
        console.log(message);
    }
  });

  ws.onClose(function() {
    console.log('connection closed');
    $scope.no_connection = true;
    $scope.nodes = [];
    $scope.nodes_status = [];
  });

  $scope.update_node_status = function(nodes_status) {
    // now = Date.parse(new Date()) / 1000.
    // nodes_status.forEach(x => {
    //   delete x.age;
    // })
    $scope.nodes_status = nodes_status;
  }

  $scope.update_system_status = function(system_status) {
    $scope.system_status = system_status;
  }

  $scope.send_command = function(command) {
    data = {
      command: command,
    }
    ws.get(data);
  }

  $scope.command_text_area = COMMAND_TEMPLATE_GCODE

  $scope.COMMAND_TEMPLATES = {
    'set valve': COMMAND_TEMPLATE_SET_VALVE,
    'home': COMMAND_TEMPLATE_HOME,
    'open dosing valve': COMMAND_TEMPLATE_OPEN_DOSING_VALVE,
    'G-Code': COMMAND_TEMPLATE_GCODE,
    'dump frame': COMMAND_TEMPLATE_DUMP_FRAME,
    'dump training holder': COMMAND_TEMPLATE_DUMP_TRAINING_HOLDER,
    'dump training dosing': COMMAND_TEMPLATE_DUMP_TRAINING_DOSING,
    'align holder': COMMAND_TEMPLATE_ALIGN_HOLDER,
    'align dosing': COMMAND_TEMPLATE_ALIGN_DOSING,
  }

  $scope.select_template = function(name) {
    $scope.command_text_area = $scope.COMMAND_TEMPLATES[name];
  }

  $scope.submit_form = function() {
    data = $scope.command_text_area;
    data.replace(/\n/g, " ");
    data = 'new Object(' + data + ')';
    data = {
      form: eval(data),
      selected_nodes: $scope.nodes.filter(x => x.selected).map(x => x.name),
    }
    // $scope.nodes.forEach(x => x.selected = false);
    console.log(data)
    ws.get(data);
  }
  $scope.nodes = []
  $scope.select_node = function(node) {
    node.selected = !node.selected;
  }

  $scope.selected_nodes_string = function() {
    return $scope.nodes.filter(x => x.selected).map(x => x.name).join(', ')
  }
  $scope.send_command_home = function(axis) {
    data = {
      form: {'verb': 'home','axis': axis,},
      selected_nodes: $scope.nodes.filter(x => x.selected).map(x => x.name),
    }
    console.log(data)
    ws.get(data);
  }

   $scope.send_system_status_running = function(value) {
     data = {
       form: {'system_running': value,},
       selected_nodes: [],
     }
     ws.get(data);
   }
   $scope.send_system_status_stop = function() {
     data = {
       form: {'system_stop': 1,},
       selected_nodes: [],
     }
     ws.get(data);
   }

   $scope.run_script = function(script_name) {
     data = {
       form: {'script': script_name,},
       selected_nodes: [],
     }
     ws.get(data);
   }
   $scope.clear_error = function(error) {
     console.log('clearing error', error);
     data = {
       form: {'clear_error': error.error_id,},
       selected_nodes: [],
     }
     ws.get(data);
   }
});



app.run(function($rootScope, $templateCache) {
  $rootScope.$on('$viewContentLoaded', function() {
    $templateCache.removeAll();
  });
});


COMMAND_TEMPLATE_SET_VALVE = "{\n\
    'verb': 'set_valves',\n\
    'valves': [0],\n\
}";

COMMAND_TEMPLATE_OPEN_DOSING_VALVE = "{\n\
    'verb': 'raw',\n\
    'data': '{out4:0}',\n\
    'wait_start': [1,3,4],\n\
    'wait_completion': true,\n\
}"

COMMAND_TEMPLATE_GCODE = "{\n\
    'verb': 'raw',\n\
    'data': '{m1:100}',\n\
    'wait_start': [1,3,4],\n\
    'wait_completion': true,\n\
}"
COMMAND_TEMPLATE_DUMP_FRAME = "{'verb': 'dump_frame'}"
COMMAND_TEMPLATE_DUMP_TRAINING_HOLDER = "{\n\
  'verb': 'dump_training_holder',\n\
  'revs': 1,\n\
  'frames_per_rev': 400,\n\
}"
COMMAND_TEMPLATE_DUMP_TRAINING_DOSING = "{\n\
  'verb': 'dump_training_dosing',\n\
  'revs': 1,\n\
  'frames_per_rev': 400,\n\
  'prepare': 1,\n\
}"
COMMAND_TEMPLATE_ALIGN_HOLDER = "{'verb': 'align', 'component': 'holder', 'retries': [5, 5, 5], 'speed': 25000}"
COMMAND_TEMPLATE_ALIGN_DOSING = "{'verb': 'align', 'component': 'dosing', 'retries': [5, 5, 5], 'speed': 25000}"
COMMAND_TEMPLATE_HOME = "{'verb': 'home'}"
