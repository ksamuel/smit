var vesselActivities = {
  setActivity: function(state, newActivity){

    if (newActivity.status) console.log('set', newActivity)
    var currentActivity = state.vesselActivities[newActivity.id];
    // update only activity if none exist already or if it's out of date
    if (!currentActivity || currentActivity.timestamp < newActivity.timestamp){
      if (newActivity.status) console.log('update')
      Vue.set(state.vesselActivities, newActivity.id, newActivity)
      return newActivity;
    }
    return currentActivity;
  },
  state: {
  }
}

var store = new Vuex.Store({
  state: {
    wamp: undefined,
    vesselActivities: vesselActivities.state,
    // keepStaleActivitiesFor:  60 * 1000 * 5, // keep vessels with no data for 5 minutes
    keepStaleActivitiesFor:  1, // don't keep vessels with no data
  },

  mutations: {

    vesselActivity: vesselActivities.setActivity,

    vesselActivities: function(state, newVesselActivities) {

      var now = (new Date().getTime());
      var timeLimit = now - state.keepStaleActivitiesFor;

      // insert all new activities
      _.forOwn(newVesselActivities, function(newActivity, id) {
        var currentActivity = vesselActivities.setActivity(state, newActivity);
        if (currentActivity) {
          currentActivity.lastSeen = now;
        }
      });

      // removed stale activities
      state.vesselActivities = _.pickBy(
        state.vesselActivities,
        function(activity, id) {
          return activity.lastSeen > timeLimit;
      });
    }
  }
});



var header = new Vue({
  el: '#header',
  data: {
    lastUpdate: 0
  },
  created: function () {
    var that = this;
    setInterval(function()  {
      that.lastUpdate += 1;
    }, 1000)
  }

});

var app = new Vue({
  el: '#app',
  store: store,

  computed: {
    incommingVessels: function () {

      var activities = this.$store.state.vesselActivities;
      var res =  _.values(_.pickBy(activities, function (activity) {
        return activity.type == "incomming";
      }));

      res.sort(function(a, b){
        if(a.sirene_time_estimate < b.sirene_time_estimate){
           return -1;
        };
        if(a.sirene_time_estimate > b.sirene_time_estimate){
           return 1;
        };
        return 0;
      })

      return res;
    },
    outgoingVessels: function () {
      var activities = this.$store.state.vesselActivities;
      var res =  _.values(_.pickBy(activities, function (activity) {
        return activity.type == "departing";
      }));

      res.sort(function(a, b){
        if(a.sirene_time_estimate < b.sirene_time_estimate){
           return -1;
        };
        if(a.sirene_time_estimate > b.sirene_time_estimate){
           return 1;
        };
        return 0;
      })

      return res;
    }
  },

  data: {
    vesselActivities: {},
    userGroups: window.USER_GROUPS
  },

  methods: {
    updateStatus: function(e, activity){

      store.wamp.call(
        'smit.activity.update.status',
        [
          activity.id,
          e.target.value
        ]
      ).then(
        function (activity) {},
        function (error) {
          console.log(error);
          alert("Cette valeur n'a pu être mise à jour. Veuillez réessayer.")
        }
      );
    },
    updateHelico: function(e, activity){

      store.wamp.call(
        'smit.vessel.update.helico',
        [
          activity.id,
          e.target.value
        ]
      ).then(
        function (activity) {},
        function (error) {
          console.log(error);
          alert("Cette valeur n'a pu être mise à jour. Veuillez réessayer.")
        }
      );
    }
  }
})

Vue.component('flashing-td', {
  template: '<td class="flash"><slot></slot></td>'
})

Vue.directive('flash', {
  update: function (el, binding, vnode, oldVnode) {
    if (binding.value != binding.oldValue){
      el.classList.add("flash");
      setTimeout(function(){
        el.classList.remove("flash");
      }, 2000)
    }
  },
})

Vue.directive('spot', {
  update: function (el, binding, vnode, oldVnode) {
    if (binding.value != binding.oldValue){
      el.classList.add("spot");
      setTimeout(function(){
        el.classList.remove("spot");
      }, 2000)
    }
  },
})


var connection = new autobahn.Connection({
  url: 'ws://127.0.0.1:3333/ws',
  realm: 'realm1'
});

connection.onopen = function (session) {
   store.wamp = session;
   console.log('Connected to server.')

   session.subscribe('smit.sirene.csv.update', function onevent(args) {
      store.commit('vesselActivities', args[0]);
      header.lastUpdate = 0;
   });

   session.subscribe('smit.activity.update', function onevent(args) {
      store.commit('vesselActivity', args[0]);
   });

};

connection.onclose = function(reason, details){
  console.log('Connection to server closed. Reason:', reason);
}

connection.open();
