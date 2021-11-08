<template>
  <div>
    <b-table
      :items="selectedActivitiesFields"
      :fields="['field', 'alternatives']">
      <template #cell(field)="data">
        {{ data.item.field.replace("_", " ") }}
      </template>
      <template #cell(alternatives)="data">
        <b-form-radio-group
          v-model="fieldsOptions[data.item.field]"
          :id="`radio-group-fields-${data.item.field}`"
          :options="alternativesAsOptions(data.item.alternatives)"
          :name="`radio-options-${data.item.field}`"
          stacked
        ></b-form-radio-group>
      </template>
    </b-table>
  </div>
</template>
<script>
export default {
  props: ['selected-activities-fields',
    'selected-activities-fields-options'],
  methods: {
    alternativesAsOptions(alternatives) {
      return Object.entries(alternatives).map(item => {
        return {'text': item[1], 'value': item[0]}
      })
    },
  },
  computed: {
    fieldsOptions: {
      get() {
        return this.selectedActivitiesFieldsOptions
      },
      set(newValue) {
        this.$emit('update:selectedActivitiesFieldsOptions', newValue)
      }
    }
  }
}
</script>
