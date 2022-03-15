<template>
  <Aggregates agg-filter="mtef-sector" label="Sector" :agg-filter-value="aggFilterValue" />
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
