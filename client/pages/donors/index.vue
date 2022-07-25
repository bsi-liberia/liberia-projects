<template>
  <div>
    <h1>Donors</h1>
    <hr />
    <AggregatesTop
      dimension="reporting-org"
      dimension-label="Donor" />
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
