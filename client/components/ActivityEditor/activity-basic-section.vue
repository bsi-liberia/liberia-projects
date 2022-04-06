<template>
    <div>
      <h2>Basic data</h2>
      <b-row>
        <b-col md="8">
          <b-form-group
            label="Dashboard ID" label-cols-sm="3"
            for="id">
            <b-input plaintext name="id" id="id"
            :value="activity.id" v-if="activity.id"></b-input>
          </b-form-group>
          <finances-input
            v-if="activity.domestic_external=='external'"
            label="Donor project code" label-cols-sm="3"
            :transaction="activity" type="text" name="iati_identifier" id="iati_identifier"
            :value.sync="activity.iati_identifier" placeholder="If known"></finances-input>
          <finances-input
            label="GoL project code" label-cols-sm="3"
            :transaction="activity" type="text" name="code" id="code"
            :value.sync="activity.code" placeholder="If known"></finances-input>
          <b-form-group
            label="Last updated" label-cols-sm="3"
            for="updated_date">
            <b-input plaintext name="updated_date" id="updated_date"
            :value="activity.updated_date" v-if="activity.updated_date"></b-input>
          </b-form-group>
        </b-col>
        <b-col md="4" v-if="activity.id && activity.domestic_external=='external'">
          <IATISearch
            :activity="activity"
            :api_routes="api_routes" />
        </b-col>
      </b-row>
      <finances-input
        label="Title" label-cols-sm="2"
        type="text" name="title" id="title"
        :value.sync="activity.title"></finances-input>
      <finances-textarea
        label="Description" label-cols-sm="2"
        name="description" id="description"
        description="Describes the overall purpose of the project and outlines its various components."
        rows="2" :value.sync="activity.description"></finances-textarea>
      <finances-textarea
        label="Objectives" label-cols-sm="2"
        name="objectives" id="objectives"
        description="Describes the specific objectives of the project in detail."
        rows="2" :value.sync="activity.objectives"></finances-textarea>
      <finances-textarea
        label="Alignment to PAPD" label-cols-sm="2"
        name="papd_alignment" id="papd_alignment"
        description="A brief description of how this project is aligned to the national development agenda"
        rows="2" :value.sync="activity.papd_alignment"></finances-textarea>
      <finances-textarea
        label="Expected deliverables" label-cols-sm="2"
        name="deliverables" id="deliverables"
        description="Describes the project's expected results"
        rows="2" :value.sync="activity.deliverables"></finances-textarea>
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
        :options="codelists.organisation" :value.sync="activity.reporting_org_id"
        :required="true">
      </finances-select>
      <organisations-section
        :activity.sync="activity"
        :codelists="codelists"
        :mode="mode"
        :api_routes="api_routes"></organisations-section>
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
                <!--
                <finances-select
                  label="Recipient Country" label-cols-sm="2"
                  name="recipient_country_code" id="recipient_country_code"
                  :options="codelists.Country" :value.sync="activity.recipient_country_code">
                </finances-select>
                -->
                <finances-select
                  label="External or Domestic Finance" label-cols-sm="2"
                  name="domestic_external" id="domestic_external"
                  :options="codelists.domestic_external" :value.sync="activity.domestic_external">
                </finances-select>
                <finances-checkbox
                  label="Published" label-cols-sm="2"
                  name="published" id="published"
                  :labels="{ true: 'Published', false: 'Unpublished' }"
                  :value.sync="activity.published">
                </finances-checkbox>
              </b-card-text>
            </b-card-body>
          </b-collapse>
        </b-card>
      </div>
    </div>
</template>
<script>
import FinancesInput from './subcomponents/finances-input.vue'
import FinancesTextarea from './subcomponents/finances-textarea.vue'
import FinancesSelect from './subcomponents/finances-select.vue'
import FinancesCheckbox from './subcomponents/finances-checkbox.vue'
import OrganisationsSection from './organisations-section.vue'
import IATISearch from './iati-search.vue'
export default {
  data() {
    return {
    }
  },
  components: {
    FinancesInput,
    FinancesTextarea,
    FinancesSelect,
    FinancesCheckbox,
    OrganisationsSection,
    IATISearch
  },
  props: ["activity", "codelists", "api_routes", "mode"],
  provide: function () {
    return {
      updateFinances: this.updateActivity
    }
  },
  methods: {
    updateActivity(_this, data, attr, value, oldValue) {
      if (this.mode=="edit") {
        var postdata = {
          type: "activity",
          attr: attr,
          value: value
        }
        this.$axios.post(this.api_routes.activity_update, postdata)
        .then(response => {
          _this.validation = true
        })
        .catch(error => {
          _this.validation = false
        })
      }
    }
  }
}
</script>