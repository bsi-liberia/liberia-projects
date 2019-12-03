// ACTIVITIES APP

Vue.config.devtools = true

Vue.component('finances-input-currency-append', {
  data() {
    return { validation: null }
  },
  delimiters: ["[[", "]]"],
  props: ["transaction", "type", "name", "placeholder", "value", "disabled", "currency"],
  template: `
    <b-form-group :state="validation">
      <b-input-group>
        <b-input-group-prepend is-text>
          <b-link title="Adjust currency and conversion rate" href="#"
            variant="outline-secondary" @click="currencyDetailPopup(transaction)">
          [[ currency ]]
          </b-link>
        </b-input-group-prepend>
        <b-input :type="type" step=".01"
          :state="validation"
          :name="name" :placeholder="placeholder"
          v-model="value" size="30" :disabled="disabled"
          v-on:change="update">
        </b-input>
        <b-input-group-append is-text>
          <b-link variant="outline-secondary" title="Adjust currency and conversion rate" href="#"
             @click="currencyDetailPopup(transaction)">
            <span class="fa fa-cog"></span>
          </b-link>
        </b-input-group-append>
      </b-input-group>
    </b-form-group>
    `,
  inject: ['updateFinances', 'currencyDetailPopup'],
  methods: {
    update(newValue, oldValue) {
      this.updateFinances(this, this.transaction, this.name, newValue, oldValue)
      this.$emit('update:value', newValue)
    },
  }
})

Vue.component('finances-radio-group', {
  data() {
    return { validation: null }
  },
  props: ["transaction", "name", "options", "value"],
  template: `
        <b-form-radio-group
          :transaction="transaction"
          v-model="value"
          :options="options"
          :name="name"
        ></b-form-radio-group>
      `,
  inject: ['updateFinances'],
  watch: {
    value: {
      handler: function(newValue, oldValue) {
        this.updateFinances(this, this.transaction, this.name, newValue, oldValue)
        this.$emit('update:value', newValue)
      }
    }
  }
})

Vue.component('finances-checkbox', {
  data() {
    return { validation: null }
  },
  delimiters: ["[[", "]]"],
  props: ["transaction", "name", "label", "value"],
  template: `
        <b-form-group :state="validation">
          <b-form-checkbox :state="validation"
            v-model="value">[[ label ]]</b-form-checkbox>
        </b-form-group>
      `,
  inject: ['updateFinances'],
  watch: {
    value: {
      handler: function(newValue, oldValue) {
        this.updateFinances(this, this.transaction, this.name, newValue, oldValue)
        this.$emit('update:value', newValue)
      }
    }
  }
})


Vue.component('finances-input', {
  data() {
    return { validation: null }
  },
  props: ["transaction", "type", "name", "placeholder", "value", "disabled", "label", "label-cols-sm"],
  template: `
    <b-form-group :state="validation"
      :label="label"
      :label-cols-sm="labelColsSm"
      :label-for="name">
      <b-input :type="type" step=".01"
      :name="name" :placeholder="placeholder"
      v-model="value" size="30" :disabled="disabled"
      v-on:change="update" :state="validation">
      </b-input>
    </b-form-group>
    `,
  inject: ['updateFinances'],
  methods: {
    update(newValue, oldValue) {
      this.updateFinances(this, this.transaction, this.name, newValue, oldValue)
      this.$emit('update:value', newValue)
    },
  }
})


Vue.component('finances-textarea', {
  data() {
    return { validation: null }
  },
  props: ["transaction", "name", "placeholder", "value", "rows", "disabled", "label", "label-cols-sm"],
  template: `
    <b-form-group :state="validation"
      :label="label"
      :label-cols-sm="labelColsSm"
      :label-for="name">
      <b-textarea :name="name" :placeholder="placeholder"
      v-model="value" :rows="rows" :disabled="disabled"
      v-on:change="update" :state="validation">
      </b-textarea>
    </b-form-group>
    `,
  inject: ['updateFinances'],
  methods: {
    update(newValue, oldValue) {
      this.updateFinances(this, this.transaction, this.name, newValue, oldValue)
      this.$emit('update:value', newValue)
    },
  }
})


Vue.component('finances-select', {
  data() {
    return { validation: null }
  },
  props: ["transaction", "name", "options", "value", "label", "label-cols-sm"],
  template: `
    <b-form-group :state="validation"
      :label="label"
      :label-cols-sm="labelColsSm"
      :label-for="name">
      <b-select :options="options" v-model="value"
      value-field="id" text-field="name"
      :state="validation">
      </b-select>
    </b-form-group>
    `,
  inject: ['updateFinances'],
  watch: {
    value: {
      handler: function(newValue, oldValue) {
        this.updateFinances(this, this.transaction, this.name, newValue, oldValue)
        this.$emit('update:value', newValue)
      }
    }
  }
})

Vue.component('forwardspends-total', {
  data() {
    return { validation: null }
  },
  props: ["data"],
  template: `
    <b-form-group :state="validation">
      <b-input type="number" step=".01"
      :name="totalValue"
      v-model="totalValue" size="30"
      :state="validation">
      </b-input>
    </b-form-group>
  `,
  computed: {
    totalValue: {
      get: function() {
        return ['Q1', 'Q2', 'Q3', 'Q4'].reduce((total, qtr) => {
          if (!(qtr in this.data.item)) { return total }
          return total + this.data.item[qtr].value
        }, 0.0)
      },
      set: function(newTotalValue) {
        var availableqtrs = ['Q1', 'Q2', 'Q3', 'Q4'].reduce((total, qtr) => {
          if (!(qtr in this.data.item)) { return total }
          total.push(qtr)
          return total
        }, [])
        availableqtrs.forEach(qtr => {
          this.data.item[qtr].value = (newTotalValue / availableqtrs.length)
        })
        console.log('updated!')
      }
    }
  }
})

Vue.component('forwardspends-quarter', {
  data() {
    return { validation: null }
  },
  props: ["quarter", "data"],
  template: `
    <b-form-group :state="validation" v-if="data.item[quarter]">
      <b-input
        type="number"
        step="0.01"
        :value="data.item[quarter].value"
        @change="updateForwardSpends"
        :state="data.item.validation"
        :state="validation"></b-input>
    </b-form-group>
    <b-form-group v-else>
      <b-input disabled></b-input>
    </b-form-group>
    `,
  methods: {
    updateForwardSpends: function(newValue) {
      var _id = this.data.item[this.quarter].id
      var _value = newValue
      axios.post(api_routes.forwardspends, {
        'id': _id,
        'value': _value
      })
      .then(response => {
        this.validation = true
      })
      .catch(error => {
        this.validation = false
      })
    },
  }
});

Vue.component('finances-subsection', {
  data() {
    return { validation: null }
  },
  delimiters: ["[[", "]]"],
  props: ["transactionType", "transactionTypeLong", "title", "addLabel",
    "financesFields", "fundSources"],
  template: `
  <b-card no-body class="mb-1">
    <b-card-header header-tag="header" role="tab">
      <b v-b-toggle="'collapse-'+transactionType">[[ title ]]</b>
    </b-card-header>
    <b-collapse :id="'collapse-'+transactionType" visible role="tabpanel">
      <b-card-body>
        <b-card-text>
          <div class="row">
            <div class="col-sm-12">
              <b-table
                :fields="financesFields"
                :items="finances[transactionTypeLong]">
                <template v-slot:cell(transaction_date)="data">
                  <finances-input
                    :transaction="data"
                    type="date"
                    name="transaction_date"
                    placeholder="yyyy-mm-dd"
                    :value.sync="data.item.transaction_date">
                  </finances-input>
                </template>
                <template v-slot:cell(transaction_value_original)="data">
                  <finances-input-currency-append
                    :transaction="data"
                    type="number"
                    name="transaction_value_original"
                    :value.sync="data.item.transaction_value_original"
                    :currency="data.item.currency"></finances-input>
                </template>
                <template v-slot:cell(transaction_value)="data">
                  <b-form-group>
                    <b-input type="text" plaintext
                      :value="(data.item.transaction_value_original * data.item.currency_rate).toLocaleString(undefined, {maximumFractionDigits:2, minimumFractionDigits: 2})"></b-input>
                  </b-form-group>
                </template>
                <template v-slot:cell(transaction_description)="data">
                  <finances-input
                    :transaction="data"
                    type="text"
                    name="transaction_description"
                    placeholder="optional"
                    :value.sync="data.item.transaction_description"
                    size="30">
                  </finances-input>
                </template>
                <template v-slot:cell(provider_org_id)="data">
                  <finances-select
                    :transaction="data"
                    name="provider_org_id"
                    :options="codelists.organisation"
                    :value.sync="data.item.provider_org_id">
                  </finances-select>
                </template>
                <template v-slot:cell(receiver_org_id)="data">
                  <finances-select
                    :transaction="data"
                    name="receiver_org_id"
                    :options="codelists.organisation"
                    :value.sync="data.item.receiver_org_id">
                  </finances-select>
                </template>
                <template v-slot:cell(aid_type)="data">
                  <finances-select
                    :transaction="data"
                    name="aid_type"
                    :options="codelists.AidType"
                    :value.sync="data.item.aid_type">
                  </finances-select>
                </template>
                <template v-slot:cell(finance_type)="data">
                  <finances-select
                    :transaction="data"
                    name="finance_type"
                    :options="codelists.FinanceType"
                    :value.sync="data.item.finance_type">
                  </finances-select>
                </template>
                <template v-slot:cell(mtef_sector)="data">
                  <finances-select
                    :transaction="data"
                    name="mtef_sector"
                    :options="codelists['mtef-sector']"
                    :value.sync="data.item.mtef_sector">
                  </finances-select>
                </template>
                <template v-slot:cell(fund_source_id)="data">
                  <b-input-group>
                    <finances-select
                      :transaction="data"
                      name="fund_source_id"
                      :options="fundSources"
                      :value.sync="data.item.fund_source_id">
                    </finances-select>
                    <b-input-group-append>
                      <b-btn size="sm" @click="addFundSource(transactionTypeLong, data.index)">
                        <span class="fa fa-plus"></span>
                      </b-btn>
                    </b-input-group-append>
                  </b-input-group>
                </template>
                <template v-slot:cell(delete)="data">
                  <b-input-text plaintext>
                    <b-button variant="link" class="text-danger"
                      size="sm" @click="deleteFinances(transactionType, data)">
                      <i class="fa fa-trash-alt"></i>
                    </b-button>
                  </b-input-text>
                </template>
              </b-table>
            </div>
          </div>
          <div class="row">
            <div class="col-sm-12 text-center">
              <b-btn variant="primary" @click="addFinances(transactionType)">
                <i class="fa fa-plus"></i>
                [[ addLabel ]]
              </b-btn>
            </div>
          </div>
        </b-card-text>
      </b-card-body>
    </b-collapse>
  </b-card>
    `,
  inject: ['finances', 'addFinances',
    'updateFinances', 'deleteFinances',
    'currencyDetailPopup', 'codelists', 'addFundSource'],
  provide: function () {
    return {
      updateFinances: this.updateFinances,
      currencyDetailPopup: this.currencyDetailPopup,
      codelists: this.codelists
    }
  },
  computed: {
    codelists() {
      return this.$root.codelists
    }
  }
})


Vue.component('counterpart-funding-section', {
  delimiters: ["[[", "]]"],
  data() {
    return {
      fields: [
        {'key': 'amount', 'label': 'Amount'},
        {'key': 'fy', 'label': 'For FY'},
        {'key': 'budgeted', 'label': 'Budgeted'},
        {'key': 'allotted', 'label': 'Allotted'},
        {'key': 'disbursed', 'label': 'Disbursed'},
        {'key': 'delete', 'label': 'Delete'}
      ],
      years: [],
      counterpartFunding: []
    }
  },
  template: `
    <div>
      <b-table :fields="fields" :items="counterpartFunding">
        <template v-slot:cell(amount)="data">
          <finances-input
            :transaction="data"
            type="number"
            name="required_value"
            placeholder="e.g. 1,000,000"
            :value.sync="data.item.required_value">
            </finances-input>
        </template>
        <template v-slot:cell(fy)="data">
          <finances-select
            :transaction="data"
            name="required_fy"
            :options="years"
            :value.sync="data.item.required_fy">
          </finances-select>
        </template>
        <template v-slot:cell(budgeted)="data">
          <finances-checkbox
            :transaction="data"
            name="budgeted"
            label="Budgeted"
            :value.sync="data.item.budgeted">
          </finances-checkbox>
        </template>
        <template v-slot:cell(allotted)="data">
          <finances-checkbox
            :transaction="data"
            name="allotted"
            label="Allotted"
            :value.sync="data.item.allotted">
          </finances-checkbox>
        </template>
        <template v-slot:cell(disbursed)="data">
          <finances-checkbox
            :transaction="data"
            name="disbursed"
            label="Disbursed"
            :value.sync="data.item.disbursed">
          </finances-checkbox>
        </template>
        <template v-slot:cell(delete)="data">
          <b-form-group>
            <b-input-text plaintext>
              <b-button variant="link" class="text-danger"
                size="sm" @click="deleteCounterpartFunding(data)">
                <i class="fa fa-trash-alt"></i>
              </b-button>
            </b-input-text>
          </b-form-group>
        </template>
      </b-table>
      <b-btn variant="primary" @click="addCounterpartFunding">
        <i class="fa fa-plus"></i>
        Add counterpart funding
      </b-btn>
    </div>
    `,
  mounted: function() {
    this.setupCounterpartFunding()
  },
  provide: function () {
    return {
      updateFinances: this.updateCounterpartFunding
    }
  },
  methods: {
    setupCounterpartFunding(data) {
      axios.get(api_routes.counterpart_funding)
        .then(res => {
          this.counterpartFunding = res.data.counterpart_funding
          this.years = res.data.fiscal_years.map(fy => {
            return {'id': fy, 'name': `FY${fy}/${parseInt(fy)+1}`}
          })
      });
    },
    addCounterpartFunding() {
      var required_value = 0.0
      var available_fys = this.counterpartFunding.map(cF => {
        return cF.required_fy
      })
      if (available_fys.length > 0) {
        var required_fy = Math.max.apply(Math, available_fys)+1
      } else {
        var required_fy = moment().date(1).format('YYYY');
      }
      axios.post(api_routes.counterpart_funding, {
        "required_value": required_value,
        "required_fy": required_fy,
        "action": "add"
      })
      .then(response => {
        this.counterpartFunding.push(response.data.counterpart_funding)
      })
    },
    deleteCounterpartFunding(data) {
      this.$bvModal.msgBoxConfirm('Are you sure you want to delete this counterpart funding entry? This action cannot be undone!', {
        title: 'Confirm delete',
        okVariant: 'danger',
        okTitle: 'Confirm delete',
        hideHeaderClose: false,
        centered: true
      })
        .then(value => {
          if (value) {
            axios.post(api_routes.counterpart_funding, {
              "id": data.item.id,
              "action": "delete"
            })
            .then(response => {
              Vue.delete(this.counterpartFunding, data.index)
            })
          }
        })
        .catch(err => {
          alert("Sorry, there was an error, and that counterpart funding entry couldn't be deleted.")
        })
    },
    updateCounterpartFunding(_this, data, attr, value, oldValue) {
      var postdata = {
        id: data.item.id,
        attr: attr,
        value: value,
        action: 'update'
      }
      axios.post(api_routes.counterpart_funding, postdata)
      .then(response => {
        _this.validation = true
        Vue.set(this.counterpartFunding, data.index, value)
      })
      .catch(error => {
        _this.validation = false
      })
    }
  }
})


Vue.component('locations-section', {
  name: 'locationsSection',
  props: ["showLocations"],
  data() {
    return {
      validation: null,
      selectedRegion: 'regions',
      regions: [],
      selectedLocations: [],
      allLocations: [],
      url: "https://d.tiles.mapbox.com/v3/markbrough.n3kod47p/{z}/{x}/{y}.png",
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
  components: {
    'l-map': window.Vue2Leaflet.LMap,
    'l-tile-layer': window.Vue2Leaflet.LTileLayer,
    'l-marker': window.Vue2Leaflet.LMarker,
    'l-popup': window.Vue2Leaflet.LPopup,
    'l-tooltip': window.Vue2Leaflet.LTooltip
  },
  delimiters: ["[[", "]]"],
  template: `
    <div>
      <div class="row" v-if="isBusy" style="margin-bottom: 20px;">
        <div class="col-sm-12 text-center">
          <b-spinner class="align-middle" label="Loading..."></b-spinner>
          <strong>Loading...</strong>
        </div>
      </div>
      <div class="row" v-if="showLocations">
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
                <i class="fa fa-exclamation-circle"></i>
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
              style="height: 400px; width: 100%;">
              <l-tile-layer :url="url"></l-tile-layer>
              <l-marker :lat-lng="marker.latlng" v-for="marker in markers">
                <l-popup>
                  [[ marker.name ]]
                </l-popup>
              </l-marker>
            </l-map>
          </div>
        </div>
      </div>
    </div>
    `,
mounted: function () {
  // We fire resize if the page height/width has
  // changed to ensure the map is corectly rendered
  // -- see below.
  window.addEventListener('resize', this.resize)
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
  showLocations: {
    immediate: true,
    handler: function(newValue, oldValue) {
      if (newValue > 0) {
        if (!(oldValue > 0)) {
          this.setupLocations()
        } else {
          this.resize()
        }
      }
    }
  },
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
    axios.post(api_routes.locations, {
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
    axios.get(api_routes.country_locations)
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
    axios.get(api_routes.locations)
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
})

Vue.component('milestones-section', {
  data() {
    return {
      fields: ['name', 'achieved', 'notes'],
      milestones: []
    }
  },
  delimiters: ["[[", "]]"],
  template: `
    <b-table
      :fields="fields"
      :items="milestones">
      <template v-slot:cell(name)="data">
        <b>[[ data.item.name ]]</b>
      </template>
      <template v-slot:cell(achieved)="data">
        <finances-checkbox
          :transaction="data"
          name="achieved"
          :value="data.item.achieved.status"
          label="Achieved">
        </finances-checkbox>
      </template>
      <template v-slot:cell(notes)="data">
        <finances-textarea
          :transaction="data"
          name="notes"
          :value="data.item.notes"
          :rows="1">
          </finances-textarea>
      </template>
    </b-table>
  `,
  mounted: function() {
    this.setupMilestones()
  },
  provide: function () {
    return {
      updateFinances: this.updateMilestones
    }
  },
  methods: {
    setupMilestones() {
      axios.get(api_routes.milestones)
      .then(response => {
        this.milestones = response.data.milestones
      })
    },
    updateMilestones(_this, data, attr, value, oldValue) {
      var postdata = {
        milestone_id: data.item.id,
        attr: attr,
        value: value,
        action: 'update'
      }
      axios.post(api_routes.milestones, postdata)
      .then(response => {
        _this.validation = true
      })
      .catch(error => {
        _this.validation = false
      })
    }
  }
})

Vue.component('finances-section', {
  template: `
  <div>
    <b-row>
      <b-col sm="9">
        <h2>Financial data</h2>
      </b-col>
      <b-col sm="3" class="text-right">
        <b-dropdown id="dropdown-form" text="Show/hide columns" ref="dropdown" right size="sm">
          <b-dropdown-form>
            <b-form-group label="Display the following columns">
              <b-form-checkbox-group
                :options="optionalSelectableFields"
                v-model="optionalSelectedFields"
              ></b-form-checkbox-group>
            </b-form-group>
          </b-dropdown-form>
        </b-dropdown>
      </b-col>
    </b-row>
    <div role="tablist">
      <finances-subsection
        :finances-fields="financesFields"
        transaction-type="C"
        transaction-type-long="commitments"
        :title="commitmentsOrAppropriations"
        :add-label="'Add ' + commitmentsOrAppropriations"
        :fund-sources="fundSources"
      ></finances-subsection>
      <finances-subsection
        v-if="activity.domestic_external=='domestic'"
        :finances-fields="financesFields"
        transaction-type="99-A"
        transaction-type-long="allotments"
        title="Allotments"
        add-label="Add allotment"
        :fund-sources="fundSources"
      ></finances-subsection>
      <finances-subsection
        :finances-fields="financesFields"
        transaction-type="D"
        transaction-type-long="disbursements"
        title="Disbursements"
        add-label="Add disbursement"
        :fund-sources="fundSources"
      ></finances-subsection>
      <b-card no-body class="mb-1">
        <b-card-header header-tag="header" role="tab">
          <b v-b-toggle.collapse-forwardspends>Forward spending plans</b>
        </b-card-header>
        <b-collapse id="collapse-forwardspends" visible role="tabpanel">
          <b-card-body>
            <b-card-text>
              <div class="row">
                <div class="col-sm-12">
                  <p class="lead">This project starts on <em>[[ activity.start_date ]]</em>
                  and ends on <em>[[ activity.end_date ]]</em>. Please provide
                  forward spend projections by quarter for the lifetime of this project.</p>
                  <p class="lead">To provide forward spend projections for earlier or later dates,
                  adjust the project start and end dates and new rows will automatically be created below.</p>
                  <p class="lead">Currency: <b>USD</b></p>
                  <b-table :fields="forwardspendFields" :items="forwardspends">
                    <template v-slot:cell(year)="data">
                      <b-form-group>
                        <b-input plaintext :value="data.item.year"></b-input>
                      </b-form-group>
                    </template>
                      <template v-slot:cell(Q1)="data">
                        <forwardspends-quarter
                          quarter="Q1" :data="data">
                        </forwardspends-quarter>
                      </template>
                      <template v-slot:cell(Q2)="data">
                        <forwardspends-quarter
                          quarter="Q2" :data="data">
                        </forwardspends-quarter>
                      </template>
                      <template v-slot:cell(Q3)="data">
                        <forwardspends-quarter
                          quarter="Q3" :data="data">
                        </forwardspends-quarter>
                      </template>
                      <template v-slot:cell(Q4)="data">
                        <forwardspends-quarter
                          quarter="Q4" :data="data">
                        </forwardspends-quarter>
                      </template>
                    </template>
                    <!--
                    <template v-slot:cell(total)="data">
                      <forwardspends-total :data="data"></forwardspends-total>
                    </template>
                    -->
                  </b-table>
                </div>
              </div>
            </b-card-text>
          </b-card-body>
        </b-collapse>
      </b-card>
    </div>
    <b-modal
      id="adjust-currency"
      title="Currency conversion settings"
      v-if="financesDetail">
      <form class="form-horizontal">
        <b-form-group
          label="Currency"
          label-cols-sm="4"
          for="currency">
          <finances-select
            :transaction="financesDetail"
            name="currency"
            :options="codelists.currency"
            :value.sync="financesDetail.item.currency">
          </finances-select>
        </b-form-group>
        <b-form-group
          label="Set conversion rate"
          label-cols-sm="4"
          for="currency_automatic">
          <finances-radio-group
            :transaction="financesDetail"
            :finances="financesDetail.item.id"
            :value.sync="financesDetail.item.currency_automatic"
            :options="currencyAutomaticOptions"
            name="currency_automatic"
          ></finances-radio-group>
        </b-form-group>
        <b-form-group
          label="Source"
          label-cols-sm="4"
          for="currency_source">
          <finances-input
            :transaction="financesDetail"
            name="currency_source"
            type="text"
            placeholder="e.g. OECD"
            :value.sync="financesDetail.item.currency_source"
            :disabled="financesDetail.item.currency_automatic">
          </finances-input>
        </b-form-group>
        <b-form-group
          label="Rate to USD"
          label-cols-sm="4"
          for="currency_rate">
          <finances-input
            :transaction="financesDetail"
            name="currency_rate"
            type="text"
            placeholder="e.g. 1"
            :value.sync="financesDetail.item.currency_rate"
            :disabled="financesDetail.item.currency_automatic">
          </finances-input>
        </b-form-group>
        <b-form-group
          label="Value date"
          label-cols-sm="4"
          for="currency_value_date">
          <finances-input
            :transaction="financesDetail"
            name="currency_value_date"
            type="date"
            :disabled="financesDetail.item.currency_automatic"
            :value.sync="financesDetail.item.currency_value_date">
          </finances-input>
        </b-form-group>
      </form>
    </b-modal>
    <b-modal
      id="add-fund-source"
      title="Add Fund Source"
      v-if="codelists"
      @ok="handleAddFundSource"
      ok-title="Add new fund source">
      <b-alert :show="newFundSource.validationErrors" variant="danger">
        All fields are required.
      </b-alert>
      <b-form-group
        label="Code"
        label-cols-sm="4"
        for="code"
        description="The code for this fund source">
        <b-input
          name="code"
          v-model="newFundSource.code"
          placeholder="e.g. TF1045"
          required>
        </b-input>
      </b-form-group>
      <b-form-group
        label="Name"
        label-cols-sm="4"
        for="name"
        description="A human-readable name for this fund source (or just repeat the code)">
        <b-input
          name="name"
          v-model="newFundSource.name"
          placeholder="e.g. Fragile States Facility, or TF1045"
          required>
        </b-input>
      </b-form-group>
      <b-form-group
        label="Finance Type"
        label-cols-sm="4"
        for="finance_type"
        description="The type of finance of this fund source (grant or loan)">
        <b-select
          :options="codelists.FinanceType"
          value-field="id" text-field="name"
          v-model="newFundSource.finance_type"
          name="finance_type"
          required>
        </b-select>
      </b-form-group>
    </b-modal>
  </div>
  `,
  delimiters: ["[[", "]]"],
  props: ["activity", "codelists"],
  data() {
    return {
      finances: {
        'commitments': [],
        'allotments': [],
        'disbursements': []
      },
      financesDetail: {
        'index': null,
        'item': {
          'transaction_id': null,
          'currency': null,
          'currency_automatic': null,
          'currency_source': null,
          'currency_rate': null,
          'currency_value_date': null
        }
      },
      forwardspends: [],
      forwardspendFields: [],
      availableFields:
        {
          'transaction_date': {'key': 'transaction_date', 'label': 'Date'},
          'transaction_value_original': {'key': 'transaction_value_original', 'label': 'Value', 'tdClass': 'nowrap'},
          'transaction_value': {'key': 'transaction_value', 'label': 'Value (USD)', 'tdClass': 'number', 'thClass': 'number'},
          'transaction_description': {'key': 'transaction_description', 'label': 'Description'},
          'provider_org_id': {'key': 'provider_org_id', 'label': 'Funder'},
          'receiver_org_id': {'key': 'receiver_org_id', 'label': 'Implementer'},
          'aid_type': {'key': 'aid_type', 'label': 'Aid Type'},
          'finance_type': {'key': 'finance_type', 'label': 'Finance Type'},
          'mtef_sector': {'key': 'mtef_sector', 'label': 'MTEF Sector'},
          'fund_source_id': {'key': 'fund_source_id', 'label': 'Fund Source', 'tdClass': 'nowrap'},
          'delete': {'key': 'delete', 'label': ''}
      },
      transaction_types: {'C': 'commitments', 'D': 'disbursements', '99-A': 'allotments'},
      defaultFields: ['transaction_date', 'transaction_value_original', 'transaction_value',
      'transaction_description', 'delete'],
      optionalSelectedFields: [],
      currencyAutomaticOptions: [
        { text: 'Automatically (recommended)', value: true },
        { text: 'Manually', value: false }
      ],
      fundSources: [],
      newFundSource: {
        code: null,
        name: null,
        finance_type: null,
        validationErrors: null
      }
    }
  },
  mounted: function() {
    this.setupFinances()
    this.setupForwardSpends()
  },
  methods: {
    currencyDetailPopup(data) {
      this.financesDetail = data
      this.$bvModal.show('adjust-currency')
    },
    setupFinances: function() {
      axios.get(api_routes.finances)
        .then(res => {
          this.finances.commitments = res.data.finances.commitments
          this.finances.allotments = res.data.finances.allotments
          this.finances.disbursements = res.data.finances.disbursements
          this.fundSources = res.data.fund_sources
          var availableFundSources = this.finances.disbursements.reduce((obj, item) => {
            if (!obj.includes(item.fund_source_id)) {
              obj.push(item.fund_source_id)
            }
            return obj
          }, [])
          if (availableFundSources.length >1) {
            this.defaultFields.push('fund_source_id')
          }
      });
    },
    setupForwardSpends: function() {
      axios.get(api_routes.forwardspends)
      .then(response => {
          this.forwardspends = response.data.forwardspends
          this.forwardspendFields = [{
              'key': 'year', 'label': 'Year'
            }].concat(response.data.quarters.map(quarter => {
            return {
              'key': quarter.quarter_name,
              'label': `${quarter.quarter_name} (${quarter.quarter_months})`
            }
          })) /*
            For now, don't show total, as it's not yet
            updating each year.

            .concat([{
              'key': 'total', 'label': 'Total'
            }])
            */
      });
    },
    addFinances: function(transaction_type) {
      var last_transaction = this.finances[this.transaction_types[transaction_type]].slice(-1)[0]
      if (last_transaction == undefined) {
        currency = "USD"
      } else {
        currency = last_transaction.currency
      }
      var transaction_date = this.last_quarter_transaction_date();
      var data = {
        "transaction_type": transaction_type,
        "transaction_date": transaction_date,
        "transaction_value": "0.00",
        "fund_source_id": last_transaction.fund_source_id,
        "currency": currency,
        "action": "add"
      }
      axios.post(api_routes.finances, data)
        .then(response => {
          if (response.data == 'False'){
              alert("There was an error updating that financial data.");
          } else {
            data = response.data;
            this.finances[this.transaction_types[transaction_type]].push(data)
          }
        }
      );
    },
    deleteFinances(transaction_type, transaction) {
      this.$bvModal.msgBoxConfirm('Are you sure you want to delete this transaction? This action cannot be undone!', {
        title: 'Confirm delete',
        okVariant: 'danger',
        okTitle: 'Confirm delete',
        hideHeaderClose: false,
        centered: true
      })
        .then(value => {
          if (value) {
            var data = {
              "transaction_id": transaction.item.id,
              "action": "delete"
            }
            axios.post(api_routes.finances, data)
            .then(returndata => {
              Vue.delete(this.finances[this.transaction_types[transaction_type]], transaction.index)
            });
          }
        })
        .catch(err => {
          alert("Sorry, there was an error, and that transaction couldn't be deleted.")
        })
    },
    updateFinances(_this, transaction, attr, value, oldValue) {
      var data = {
        'finances_id': transaction.item.id,
        'attr': attr,
        'value': value,
      }
      axios.post(api_routes.finances_update, data)
      .then(response => {
        var data = response.data
        // Because there can be a delay in getting data back
        // from the API, we only want to update `finances` for
        // certain fields.
        // If it's automatic and date or currency changed
        // or if automatic is set to true
        var updateFields = ['transaction_date', 'currency']
        if (
            ((updateFields.includes(attr)) && (transaction.item.currency_automatic == true)) ||
            ((attr=='currency_automatic') && (value = true))
           ) {
          var finances_long_name = this.transaction_types[transaction.item.transaction_type]
          var copyData = this.finances[this.transaction_types[transaction.item.transaction_type]][transaction.index]
          copyData.currency_rate = data.currency_rate
          copyData.currency_source = data.currency_source
          copyData.currency_value_date = data.currency_value_date
          Vue.set(this.finances[finances_long_name], transaction.index, copyData)
        }
        _this.validation = true
      }).catch(error => {
        console.log(`Error trying to update attribute ${attr} with value ${value}, the error was: ${ error }`)
        _this.validation = false
      }
      )
    },
    last_quarter_transaction_date: function() {
      return moment().date(1).subtract(1, 'quarter').endOf('quarter').format('YYYY-MM-DD');
    },
    addFundSource: function(transaction_type, finance_index) {
      this.$bvModal.show('add-fund-source')
      this.newFundSource.transaction_type = transaction_type
      this.newFundSource.finance_index = finance_index
    },
    handleAddFundSource(bvModalEvt) {
      bvModalEvt.preventDefault()
      if (this.newFundSource.code && this.newFundSource.name && this.newFundSource.finance_type) {
        this.newFundSource.validationErrors = false
        axios.post(api_routes.codelists,
        {
          'method': 'add',
          'codelist': 'fund-source',
          'code': this.newFundSource.code,
          'name': this.newFundSource.name,
          'finance_type': this.newFundSource.finance_type
        })
        .then(response => {
          // Add to list of available fund sources
          this.fundSources.push({'id': response.data.id, 'name': this.newFundSource.name})
          // Change that row to use this new fund source
          var ft = this.finances[this.newFundSource.transaction_type][this.newFundSource.finance_index]
          ft.fund_source_id = response.data.id
          Vue.set(this.finances[this.newFundSource.transaction_type], this.newFundSource.finance_index, ft)
          this.$bvModal.hide('add-fund-source')
        })
        .catch(error => {
          alert(`There was an error adding that fund source. Please check this fund source doesn't already exist and try again.`)
          console.log('Error adding fund source', error)
        })
      } else {
        this.newFundSource.validationErrors = true
      }
    }
  },
  computed: {
    commitmentsOrAppropriations() {
      if (this.activity.domestic_external == 'domestic') {
        return 'Appropriations'
      } else {
        return 'Commitments'
      }
    },
    optionalSelectableFields() {
      return Object.values(this.availableFields).reduce((fields, field) => {
        if (!(this.defaultFields.includes(field.key))) {
          fields.push({'value': field.key, 'text': field.label})
        }
        return fields
      }, [])
    },
    financesFields() {
      // Displayed fields are determined by default fields
      // plus any that are optionally selected.
      // We do it this way so that they are displayed in the order
      // listed in this.availableFields.
      return Object.values(this.availableFields).reduce((fields, field) => {
        if (this.defaultFields.concat(this.optionalSelectedFields).includes(field.key)) {
          fields.push(field)
        }
        return fields
      }, [])
    }
  },
  provide: function () {
    return {
      addFinances: this.addFinances,
      updateFinances: this.updateFinances,
      deleteFinances: this.deleteFinances,
      finances: this.finances,
      currencyDetailPopup: this.currencyDetailPopup,
      addFundSource: this.addFundSource
    }
  }
})


Vue.component('organisations-section', {
  data() {
    return {
    }
  },
  delimiters: ["[[", "]]"],
  props: ["activity", "codelists"],
  template: `
    <div id="organisations">
      <b-form-group
        :label="role.name"
        label-cols-sm="2"
        v-for="role in activity.organisations">
        <finances-select
          :transaction="organisation"
          name="organisation_id"
          :options="codelists.organisation"
          :value.sync="organisation.id"
          v-for="organisation in role.entries"></finances-select>
      </b-form-group>
    </div>
  `,
  mounted: function() {
  },
  provide: function () {
    return {
      updateFinances: this.updateOrganisation
    }
  },
  methods: {
    updateOrganisation(_this, data, attr, value, oldValue) {
      if (this.$root.mode=="edit") {
        var postdata = {
          type: "organisation",
          activityorganisation_id: data.activityorganisation_id,
          attr: attr,
          value: value
        }
        axios.post(api_routes.activity_update, postdata)
        .then(response => {
          _this.validation = true
        })
        .catch(error => {
          _this.validation = false
        })
      }
    }
  }
})


Vue.component('sectors-section', {
  data() {
    return {
    }
  },
  delimiters: ["[[", "]]"],
  props: ["activity", "codelists"],
  template: `
    <div>
      <h2>Sectors</h2>
      <b-form-group
        :label="classification.name"
        label-cols-sm="3"
        v-for="classification in activity.classifications">
        <finances-select
          :transaction="code"
          name="codelist_code_id"
          :options="codelists[classification.codelist]"
          :value.sync="code.code"
          v-for="code in classification.entries"></finances-select>
      </b-form-group>
    </div>
  `,
  mounted: function() {
  },
  provide: function () {
    return {
      updateFinances: this.updateSector
    }
  },
  methods: {
    updateSector(_this, data, attr, value, oldValue) {
      if (this.$root.mode=="edit") {
        var postdata = {
          type: "classification",
          activitycodelist_id: data.activitycodelist_id,
          attr: attr,
          value: value
        }
        axios.post(api_routes.activity_update, postdata)
        .then(response => {
          _this.validation = true
        })
        .catch(error => {
          _this.validation = false
        })
      }
    }
  }
})


Vue.component('activity-basic-section', {
  data() {
    return {
    }
  },
  delimiters: ["[[", "]]"],
  props: ["activity", "codelists"],
  template: `
    <div>
      <h2>Basic data</h2>
      <finances-input
       label="Project code" label-cols-sm="2"
       :transaction="activity" type="text" name="code" id="code"
        :value.sync="activity.code" placeholder="If known"></finances-input>
      <b-form-group
        label="Last updated" label-cols-sm="2"
        for="updated_date">
        <b-input plaintext name="updated_date" id="updated_date"
        :value="activity.updated_date" v-if="activity.updated_date"></b-input>
      </b-form-group>
      <finances-input
        label="Title" label-cols-sm="2"
        type="text" name="title" id="title"
        :value.sync="activity.title"></finances-input>
      <finances-textarea
        label="Description" label-cols-sm="2"
        name="description" id="description"
        rows="2" :value.sync="activity.description"></finances-textarea>
      <finances-input
        label="Start date" label-cols-sm="2"
        type="date" name="start_date" id="start_date"
        :value.sync="activity.start_date" placeholder="yyyy-mm-dd">
      </finances-input>
      <finances-input
        label="End date" label-cols-sm="2"
        type="date" name="end_date" id="end_date"
        :value.sync="activity.end_date"
        placeholder="yyyy-mm-dd">
      </finances-input>
      <finances-select
        label="Activity Status" label-cols-sm="2"
        name="activity_status" id="activity_status"
        :options="codelists.ActivityStatus" :value.sync="activity.activity_status">
      </finances-select>
      <finances-select
        label="Aid Type" label-cols-sm="2"
        name="aid_type" id="aid_type"
        :options="codelists.AidType" :value.sync="activity.aid_type">
      </finances-select>
      <finances-select
        label="Finance Type" label-cols-sm="2"
        name="finance_type" id="finance_type"
        :options="codelists.FinanceType" :value.sync="activity.finance_type">
      </finances-select>
      <hr />
      <h3>Organisations</h3>
      <finances-select
        label="Reported by" label-cols-sm="2"
        name="reporting_org_id" id="reporting_org_id"
        :options="codelists.organisation" :value.sync="activity.reporting_org_id">
      </finances-select>
      <organisations-section
        :activity.sync="activity" :codelists="codelists"></organisations-section>
      <hr/>
      <div role="tablist">
        <b-card no-body>
          <b-card-header header-tag="header" role="tab">
            <b-button block href="#" v-b-toggle.detailed variant="outline-secondary">Adjust default settings</b-button>
          </b-card-header>
          <b-collapse id="detailed" role="tabpanel">
            <b-card-body>
              <b-card-text>
                <finances-select
                  label="Collaboration Type" label-cols-sm="2"
                  name="collaboration_type" id="collaboration_type"
                  :options="codelists.CollaborationType" :value.sync="activity.collaboration_type">
                </finances-select>
                <finances-select
                  label="Recipient Country" label-cols-sm="2"
                  name="recipient_country_code" id="recipient_country_code"
                  :options="codelists.Country" :value.sync="activity.recipient_country_code">
                </finances-select>
                <finances-select
                  label="External or Domestic Finance" label-cols-sm="2"
                  name="domestic_external" id="domestic_external"
                  :options="codelists.domestic_external" :value.sync="activity.domestic_external">
                </finances-select>
              </b-card-text>
            </b-card-body>
          </b-collapse>
        </b-card>
      </div>
    </div>
  `,
  provide: function () {
    return {
      updateFinances: this.updateActivity
    }
  },
  methods: {
    updateActivity(_this, data, attr, value, oldValue) {
      if (this.$root.mode=="edit") {
        var postdata = {
          type: "activity",
          attr: attr,
          value: value
        }
        axios.post(api_routes.activity_update, postdata)
        .then(response => {
          _this.validation = true
        })
        .catch(error => {
          _this.validation = false
        })
      }
    }
  }
})


const router = new VueRouter({
})

new Vue({
  router,
  el: "#app",
  delimiters: ["[[", "]]"],
  data() {
    return {
      isBusy: true,
      path: this.$route.path,
      showLocations: 0,
      activity: null,
      mode: activityEditorMode,
      codelists: {
      }
    }
  },
  mounted: function() {
    this.setupCodelists()
    this.getActivity()
  },
  watch: {
    $route: {
      immediate: true,
      handler: function(newValue) {
        if (newValue.path === '/locations') {
          this.showLocations +=1
        }
      }
    }
  },
  methods: {
    setDocumentTitle: function() {
      if (this.mode == 'new') {
        document.title = "New activity | Liberia Project Dashboard"
      } else {
        document.title = `Edit activity ${this.activity.title} | Liberia Project Dashboard`
      }
    },
    getActivity: function() {
      axios.get(api_routes.activity)
        .then(response => {
          this.activity = response.data.activity
          this.isBusy = false
          this.setDocumentTitle()
        })
    },
    setupCodelists: function() {
      axios.get(api_routes.codelists)
        .then(response => {
          this.codelists = response.data.codelists
          this.codelists.organisation = response.data.organisations
        })
    },
    saveNewActivity: function() {
      axios.post(api_routes.activity_update, this.activity)
      .then(response => {
        window.location.href = response.data.url_edit
      })
      .catch(error => {
        alert(error)
      })
    }
  }
})

/*

$(document).on("click", "#search_iati", function(e) {
    e.preventDefault();
    var title = $("#title").val();
    var reporting_org_code = $("#reporting_org_id option:selected")[0].getAttribute("data-organisation-code");
    var reporting_org_name = $("#reporting_org_id option:selected")[0].getAttribute("data-name");
    console.log(reporting_org_code);
    $('#iati-search-results-modal').modal();
    search_for_iati_data(title, reporting_org_code, reporting_org_name);
});
$(document).on("click", "#search_modal_button", function(e) {
    e.preventDefault();
    var title = $("#search_modal_title").val();
    var reporting_org_code = $("#reporting_org_id option:selected")[0].getAttribute("data-organisation-code");
    var reporting_org_name = $("#reporting_org_id option:selected")[0].getAttribute("data-name");
    search_for_iati_data(title, reporting_org_code, reporting_org_name);
  }
)
function search_for_iati_data(title, reporting_org_code, reporting_org_name) {
  $("#iati-search-results-area").html('<p class="text-muted">Loading...</p>');
  var data = {
  "title": title,
  "reporting_org_code": reporting_org_code
  }
  $.get(api_routes.iati_search, data,
    function(returndata){
      if (returndata["count"] == '0'){
        var results = null;
      } else {
        var results = returndata["results"];
      }
        // Render locations selector
        var iati_results_template = $('#iati-search-results-template').html();
        Mustache.parse(iati_results_template);
        var rendered_search_results = Mustache.render(iati_results_template, {
          "title": title, "reporting_org": reporting_org_name, "results": results});
        $('#iati-search-results-area').html(rendered_search_results);
    }
  );
}

$(document).on("click", "#iati-search-results-area .import a",
  function(e) {
  e.preventDefault();
  tr = $(this).closest("tr")
  iati_identifier = tr.find("td.iati_identifier a").html().trim();
  description = tr.find("td.description").html();
  $("#code").val(iati_identifier);
  //$("#description").val(description);
  $('#iati-search-results-modal').modal('hide');
  $("#code").trigger("change");
  //$("#description").trigger("change");
  var data = {
    "iati_identifier": iati_identifier
  }
  $.get(api_routes.iati_fetch_data, data,
    function(returndata){
      if (returndata == 'True'){
        alert("Found documents for this activity! Reload the page to see them.");
      } else {
        alert("No documents found for this activity.")
      }
    }
  );
});
*/
