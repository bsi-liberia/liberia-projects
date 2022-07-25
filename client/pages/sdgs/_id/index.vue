<template>
  <Aggregates agg-filter="sdg-goals" label="Sustainable Development Goals" :agg-filter-value="aggFilterValue" />
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
