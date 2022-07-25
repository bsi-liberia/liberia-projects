<template>
  <div>
    <h1>Sectors</h1>
    <hr />
    <AggregatesTop
      dimension="mtef-sector"
      dimension-label="Sector" />
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
