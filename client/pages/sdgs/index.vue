<template>
  <div>
    <h1>Sustainable Development Goals</h1>
    <hr />
    <AggregatesTop
      dimension="sdg-goals"
      dimension-label="SDG" />
  </div>
</template>
<script>
import AggregatesTop from '~/components/AggregatesTop.vue'
export default {
  components: {
    AggregatesTop
  }
}
</script>
