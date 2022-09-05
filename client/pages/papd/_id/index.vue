<template>
  <Aggregates agg-filter="papd-pillar" label="Pro-Poor Agenda for Prosperity and Development" :agg-filter-value="aggFilterValue" />
</template>
<script>
import Aggregates from '~/components/Aggregates.vue'
export default {
  components: {
    Aggregates
  },
  computed: {
    aggFilterValue() {
      return this.$route.params.id
    }
  }
}
</script>
