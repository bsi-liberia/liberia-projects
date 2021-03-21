<template>
  <div>
    <b-modal id="add-organisation"
      title="Add Organisation"
      ok-title="Add new"
      @ok="addOrganisation"
      size="lg">
      <b-alert variant="danger" :show="newOrganisation.validation.name == false">
        The name field is required.
      </b-alert>
      <b-alert variant="danger" :show="newOrganisation.validation._type == false">
        The type field is required.
      </b-alert>
      <b-form-group
        label="Name"
        label-cols-sm="3"
        :state="newOrganisation.validation.name">
        <b-input v-model="newOrganisation.name" required :state="newOrganisation.validation.name">
        </b-input>
      </b-form-group>
      <b-form-group
        label="IATI Organisation Code"
        label-cols-sm="3"
        description="Leave blank if unknown">
        <b-input v-model="newOrganisation.code">
        </b-input>
      </b-form-group>
      <b-form-group
        label="GoL Organisation Code"
        label-cols-sm="3"
        description="Leave blank if unknown">
        <b-input v-model="newOrganisation.budget_code">
        </b-input>
      </b-form-group>
      <b-form-group
        label="Type"
        label-cols-sm="3">
        <b-select v-model="newOrganisation._type"
        :options="organisationTypeOptions"
        :state="newOrganisation.validation._type"></b-select>
      </b-form-group>
      <template v-if="similarOrganisations.length>0">
        <hr />
        <b-alert show variant="warning">
          <p>Please check that this organisation doesn't already exist &ndash; here
          are the closest matches. If you wish, you can select one of these organisations.</p>
        </b-alert>
        <b-table
          :items="similarOrganisations"
          :fields="similarOrganisationsFields"
          :busy="isBusy">
          <template v-slot:table-busy>
            <div class="text-center my-2">
              <b-spinner class="align-middle" label="Loading..."></b-spinner>
              <strong>Loading...</strong>
            </div>
          </template>
          <template v-slot:cell(select)="data">
            <b-btn @click="selectOrganisation(data.item.id)" size="sm">
              <font-awesome-icon :icon="['fa', 'check-circle']" />
              Select
            </b-btn>
          </template>
        </b-table>
      </template>
    </b-modal>
  </div>
</template>
<script>
import { debounce } from 'vue-debounce'
import Vue from 'vue'
export default {
  name: 'AddOrganisationModal',
  middleware: 'auth',
  loading: false,
  components: {
  },
  props: ["codelists", "activity", "role"],
  data() {
    return {
      isBusy: false,
      newOrganisation: {
        name: null,
        code: null,
        budget_code: null,
        _type: null,
        validation: {
          name: null,
          type: null,
        }
      },
      organisationTypeOptions: [
        {
          'text': 'Donor',
          'value': 'donor'
        },
        {
          'text': 'NGO',
          'value': 'ngo'
        },
        {
          'text': 'GoL',
          'value': 'gol'
        }
      ],
      similarOrganisations: [],
      similarOrganisationsFields: ['name', 'select']
    }
  },
  computed: {
    organisations: {
      get() {
        return this.codelists.organisation
      },
      set(organisation) {
        return Vue.set(this.codelists, 'organisation', organisation)
      }
    }
  },
  methods: {
    selectOrganisation(organisation_id) {
      this.activity.organisations[this.role]['entries'][0].id = organisation_id
      this.$bvModal.hide('add-organisation')
      //Vue.set(this.activity, 'organisations', organisations)
    },
    checkOrganisationExists: debounce(function (e) {
      this.isBusy = true
      this.$axios
        .post('organisations/search_similar/', {
          organisation_name: this.newOrganisation.name
        })
        .then(response => {
          this.similarOrganisations = response.data.organisations
          this.isBusy = false
        })
    }, 500),
    addOrganisation(bvEvent) {
      bvEvent.preventDefault()
      this.newOrganisation.validation.name = null
      this.newOrganisation.validation._type = null
      if (!this.newOrganisation.name) {
        this.newOrganisation.validation.name = false
      }
      if (!this.newOrganisation._type) {
        this.newOrganisation.validation._type = false
      }
      if ((this.newOrganisation.name != null) && (this.newOrganisation._type != null)) {
        const data = {
          name: this.newOrganisation.name,
          code: this.newOrganisation.code,
          budget_code: this.newOrganisation.budget_code,
          _type: this.newOrganisation._type
        }
        this.$axios.post(`codelists/organisations/new/`, data)
         .then(response => {
          this.codelists.organisation.push(response.data.organisation)
          this.selectOrganisation(response.data.organisation.id)
          this.$bvModal.hide('add-organisation')
        })
      }
    }
  },
  watch: {
    'newOrganisation.name': {
      handler: function(newValue) {
        this.similarOrganisations = []
        this.checkOrganisationExists(newValue)
      }
    }
  },
}
</script>