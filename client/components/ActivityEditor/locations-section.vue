<template>
  <div>
    <div class="row" v-if="isBusy" style="margin-bottom: 20px;">
      <div class="col-sm-12 text-center">
        <b-spinner class="align-middle" label="Loading..."></b-spinner>
        <strong>Loading...</strong>
      </div>
    </div>
    <div class="row" v-if="$route.query.tab=='locations'">
      <div class="col-sm-4">
        <div id="locations-selector">
          <b-form-group
            label="Display:"
            label-cols-sm="3"
            label-for="region-selector">
            <b-select name="region-selector" :options="regions"
              v-model="selectedRegion">
              <template v-slot:first>
                <option :value="null">All locations</option>
                <option value="regions">Regions</option>
              </template>
            </b-select>
          </b-form-group>
        </div>
        <div id="location-data">
          <div id="locationSelector">
            <b-form-group v-if="regionOptions.length > 0">
              <b-form-checkbox-group
              v-model="selectedLocations"
              :options="regionOptions"
              stacked
              buttons
              button-variant="outline-secondary"
              style="width: 100%; text-align: left;"
              ></b-form-checkbox-group>
            </b-form-group>
            <b-alert variant="warning" show v-else>
              <font-awesome-icon :icon="['fa', 'exclamation-circle']" />
              No locations found.
            </b-alert>
          </div>
        </div>
      </div>
      <div class="col-sm-8">
        <div id="location-container">
          <l-map
            ref="activityMap"
            :options="mapOptions"
            :dragging="dragging"
            :tap="tap"
            :maxZoom="maxZoom"
            :bounds="bounds"
            :zoom="zoom"
            style="height: 400px; width: 100%;"
            lazy>
            <l-tile-layer :url="url"></l-tile-layer>
            <l-marker :lat-lng="marker.latlng" v-for="marker in markers" v-bind:key="marker.id">
              <l-popup>
                {{ marker.name }}
              </l-popup>
            </l-marker>
          </l-map>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  name: 'locationsSection',
  props: ["api_routes"],
  data() {
    return {
      validation: null,
      selectedRegion: 'regions',
      regions: [],
      selectedLocations: [],
      allLocations: [],
      url: "https://api.mapbox.com/styles/v1/markbrough/ckhe9jol304hs19pd9xkkswsf/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoibWFya2Jyb3VnaCIsImEiOiJUZXFjRHowIn0.8e3Fq018PP1x5QMTxa8n_A",
      mapOptions: {
        zoomSnap: 0.5
      },
      zoom: 5,
      maxZoom: 15,
      dragging: false,
      tap: false,
      isBusy: true
    }
  },
  mounted: function () {
    this.setupLocations()
  },
  watch: {
    // We mount the component on page load, but we only
    // fire this.setupLocations() once the tab is clicked
    // on and the value of `showLocations` turns to true.
    // We have to fire resize() each time the tab is shown
    // in case it has been resized on other tabs.
    // This is due to a nasty bug which would otherwise
    // not load the tiles correctly:
    // https://github.com/KoRiGaN/Vue2Leaflet/issues/96
    // NB this seems to be OK now as long as the component
    // is not rendered on page load (i.e. when the tab is hidden)
    selectedLocations: {
      handler: function(newValue, oldValue) {
        if (!(this.isBusy)) {
          if (newValue.length > oldValue.length) {
            var _add = newValue.filter(nv => {
              return (!(oldValue.includes(nv)))
            })
            _add.forEach(item => {
              this.addDeleteLocation('add', item)
            })
          } else {
            var _del = oldValue.filter(ov => {
              return (!(newValue.includes(ov)))
            })
            _del.forEach(item => {
              this.addDeleteLocation('delete', item)
            })
          }
        }
      }
    }
  },
  computed: {
    bounds() {
      if (Object.keys(this.locationsObj) == 0) {
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
    locationsObj() {
      return this.allLocations.reduce((obj, location) => {
        obj[location.id] = location
        return obj
      }, {})
    },
    markers() {
      if (Object.keys(this.locationsObj) == 0) { return [] }
      return this.selectedLocations.map(location_id => {
        var location = this.locationsObj[location_id]
        location['latlng'] = L.latLng(
            location.latitude,
            location.longitude
          )
        return location
      })
    },
    regionOptions() {
      if (this.selectedRegion == null) {
        var locations = this.allLocations
      }
      else if (this.selectedRegion == 'regions') {
        var locations = this.allLocations.filter(location => {
          return location.feature_code == 'ADM1'
        })
      } else {
        var locations = this.allLocations.filter(location => {
          return location.admin1_code == this.selectedRegion
        })
      }
      var region_ordering = this.regions.reduce((ordering, region, index) => {
        ordering[region.admin1_code] = index
        return ordering
      }, {})
      return locations.map(location => {
        return {
            'value': location.id,
            'text': location.name,
            'admin1_code': location.admin1_code,
            'feature_code': location.feature_code
        }
      }).sort((a,b) => {
        if (a.admin1_code == b.admin1_code) {
          if (a.feature_code == b.feature_code) {
            return a.text > b.text
          } else {
            return a.feature_code > b.feature_code
          }
        }
        return region_ordering[a.admin1_code] > region_ordering[b.admin1_code]
      })
    }
  },
  methods: {
    resize() {
      if ('activityMap' in this.$refs) {
        this.$refs.activityMap.mapObject.invalidateSize()
      }
    },
    addDeleteLocation(action, location_id) {
      this.$axios.post(this.api_routes.locations, {
          "action": action,
          "location_id": location_id
        })
      .then(response => {
        if (response.data == 'False'){
            alert("There was an error updating that location.");
        }
      })
    },
    setupLocations() {
      this.$axios.get(this.api_routes.country_locations)
        .then(response => {
          this.allLocations = response.data.locations
          this.regions = response.data.locations.filter(region => {
            return region.feature_code == 'ADM1'
          }).map(region => {
            return {
              'value': region.admin1_code,
              'text': region.name,
              'admin1_code': region.admin1_code
          }
          }).sort((a,b) => {
            return (a.text > b.text)
          })
        })
      this.$axios.get(this.api_routes.locations)
        .then(response => {
          this.selectedLocations = response.data.locations.map(location => {
            return location.location_id
          })
        })
        .finally(f => {
          this.isBusy = false
        })
    }
  }
}
</script>