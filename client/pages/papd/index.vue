<template>
  <div>
    <h1>Pro-Poor Agenda for Prosperity and Development</h1>
    <hr />
    <AggregatesTop
      dimension="papd-pillar"
      dimension-label="PAPD Pillar" />
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
      title: `Pro-Poor Agenda for Prosperity and Development | ${this.$config.title}`,
      meta: [
        { hid: 'twitter:title', name: 'twitter:title', content: `Pro-Poor Agenda for Prosperity and Development | ${this.$config.title}` },
        { hid: 'og:title', name: 'og:title', content: `Pro-Poor Agenda for Prosperity and Development | ${this.$config.title}` },
      ]
    }
  }
}
</script>
