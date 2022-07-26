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
  },
  head() {
    return {
      title: `Donors | ${this.$config.title}`,
      meta: [
        { hid: 'twitter:title', name: 'twitter:title', content: `Donors | ${this.$config.title}` },
        { hid: 'og:title', name: 'og:title', content: `Donors | ${this.$config.title}` },
      ]
    }
  }
}
</script>
