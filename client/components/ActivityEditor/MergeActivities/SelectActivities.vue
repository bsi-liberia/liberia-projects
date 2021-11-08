<template>
  <div>
    <b-table
      :items="similarActivities"
      :fields="['title', 'selected']"
      :tbody-tr-class="rowClassStep2">
      <template #cell(title)="data">
        <nuxt-link
          :to="{ name: 'activities-id', params: { id: data.item.id}}"
          target="_blank">
          {{ data.item.title }}
        </nuxt-link>
        <code v-if="data.item.iati_identifier">{{ data.item.iati_identifier }}</code>
      </template>
      <template #cell(selected)="data">
        <b-form-checkbox
          v-model="selectedActivities"
          name="selected-activities"
          :value="data.item.id"
          :disabled="data.item.id==activity.id">Select activity</b-form-checkbox>
      </template>
    </b-table>
  </div>
</template>
<script>
export default {
  props: ['similar-activities', 'selected-activities', 'activity'],
}
</script>