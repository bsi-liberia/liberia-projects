<template>
  <div>
    <template v-if="isBusy">
      <b-row style="margin-bottom: 20px;">
        <b-col md="12" class="text-center">
          <b-spinner class="align-middle" label="Loading..."></b-spinner>
          <strong>Loading...</strong>
        </b-col>
      </b-row>
    </template>
    <template v-else>
      <div id="locationMap">
        <l-map
          ref="activityMap"
          :options="mapOptions"
          :dragging="dragging"
          :tap="tap"
          :maxZoom="maxZoom"
          :bounds="bounds"
          :zoom="zoom">
          <l-tile-layer :url="url"></l-tile-layer>
          <v-marker-cluster :options="{chunkedLoading: true, showCoverageOnHover: false}">
            <l-marker :lat-lng="marker.latlng" v-for="marker in allLocations" v-bind:key="marker.locationID">
              <l-popup>
                <b>{{ marker.name }}</b><br />
                <nuxt-link :to="{ name: 'activities-id', params: {id: marker.id }}">{{ marker.title }}</nuxt-link>
              </l-popup>
            </l-marker>
          </v-marker-cluster>
        </l-map>
      </div>
    </template>
  </div>
</template>
<style scoped>
#locationMap {
  height: 400px;
}
</style>
<script>
export default {
  data() {
    return {
      validation: null,
      allLocations: [],
      url: "https://d.tiles.mapbox.com/v3/markbrough.n3kod47p/{z}/{x}/{y}.png",
      mapOptions: {
        zoomSnap: 0.,
        scrollWheelZoom: false
      },
      zoom: 5,
      maxZoom: 15,
      dragging: false,
      tap: false,
      isBusy: true
    }
  },
  head() {
    return {
      link: [
        {
          rel: "stylesheet",
          href:
            "https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.4.1/MarkerCluster.Default.css"
        },
        {
          rel: "stylesheet",
          href:
            "https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.4.1/MarkerCluster.css"
        }
      ]
    };
  },
  mounted: function () {
    // We fire resize if the page height/width has
    // changed to ensure the map is corectly rendered
    // -- see below.
    //window.addEventListener('resize', this.resize)
    this.setupLocations()
  },
  computed: {
    bounds() {
      if (this.allLocations.length == 0) {
        return L.latLngBounds([
          [ 4.38333, -11.3242 ],
          [ 8.37583, -7.56658 ]
        ])
       }
      var lats = this.allLocations.map(location => {
        return location.latitude
      })
      var longs = this.allLocations.map(location => {
        return location.longitude
      })
      return L.latLngBounds([
          [Math.min.apply(null, lats), Math.min.apply(null, longs)],
          [Math.max.apply(null, lats), Math.max.apply(null, longs)]
      ]);
    },
  },
  methods: {
    resize() {
      if ('activityMap' in this.$refs) {
        this.$refs.activityMap.mapObject.invalidateSize()
      }
    },
    setupLocations() {
      this.$axios.get(`activity_locations/`)
        .then(response => {
          this.allLocations = response.data.locations
        })
        .finally(f => {
          this.isBusy = false
        })
    }
  }
}
</script>