<template>
  <b-form-group state="validation">
    <b-select
    class="form-control" :options="permissionValues"
    text-field="name" v-model="permission_value"
    :state="validation">
    </b-select>
  </b-form-group>
</template>
<script>
export default {
  data() {
    return {
      validation: null
    }
  },
  props: ["permission_id", "permission_value", "permissionValues", "updateChangedPermission"],
  watch: {
    'permission_value': {
      handler: function(newValue) {
        this.updateChangedPermission(this, this.permission_id, 'permission_value', newValue)
        this.$emit('update:permission_value', newValue)
      }
    }
  }
}
</script>