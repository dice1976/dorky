$(document).ready(function () {

  console.log('== Dorky.');

  $('#result_modal').modal({show: false});

  $('#create_new').click(function () { edit_dork(); });

  dorks = [];
  categories = [];

  search_engines = ['google', 'google_customsearch', 'bing', 'shodan'];

  $.post('/get', {what: 'dorks'}, function (resp) {
    dorks = resp.dorks;
    categories = resp.categories;
    show_categories();
    show_dorks();
  });


  function show_categories() {
    $.each(categories, function (i, cat) {
      $('#categories').append($('<td>')
        .append($('<a>', {
          href: '#',
          text: cat,
          click: function () {
            filter_cat(cat);
            return null;
          }
        }))
      )
    });
  }

  function show_dorks() {
    var tbl = $('#dorks');
    $.each(dorks, function (i, dork) {
      var tr = $('<tr>', {dbid: dork._id.$oid})
        .append($('<td>')
          .append($('<a>', {
            text: 'Edit',
            click: function () {
              edit_dork(dork);
              return null;
            }
          }))
        )
        .append($('<td>', {text: dork.query}))
        .append($('<td>', {text: dork.description}))
        .append($('<td>', {text: dork.category}))
        .append($('<td>', {text: dork.search_engine}))
        .append($('<td>')
          .append($('<a>', {href: dork.source, text: dork.source}))
        )
        .append($('<td>')
          .append($('<span>', {
            id: 'disabled_' + dork._id.$oid,
            click: function () {
              set_disabled(dork._id.$oid, !dork.disabled);
              return null;
            },
            class: "label label-" + ((dork.disabled)? 'danger' : 'success'),
            text: ((!dork.disabled)? 'Yes' : 'No')
          }))
        )
        .append($('<td>')
          .append($('<a>', {
            class: 'view_results',
            dbid: dork._id.$oid,
            text: 'Show'
          }))
        );
      tbl.append(tr);
    });
    $('.view_results').each(function (i) {
      $(this).click(function () {
        var dbid = $(this).attr('dbid');
        $.post('/get', {dbid: dbid, what: 'results'}, function (response) {
          var tbl = $('<table>', {class: 'table', style: 'overflow: auto;'});
          $.each(response.results, function (i, row) {
            tbl.append($('<tr>')
              .append($('<td>', {text: row.result.title}))
              .append($('<td>', {text: row.result.summary}))
              .append($('<td>', {text: row.engine_id})));
          });
          $('#result_modal .modal-body').empty().append(tbl);
          $('#result_modal .modal-title').text(dbid);
          $('#result_modal').modal('show');
        });
        return false;
      });
    });
  }

  function uppercase_first (str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  function categoryMatcher(q, cb) {
    var matches, substringRegex;

    // an array that will be populated with substring matches
    matches = [];

    // regex used to determine if a string contains the substring `q`
    substrRegex = new RegExp(q, 'i');

    // iterate through the pool of strings and for any string that
    // contains the substring `q`, add it to the `matches` array
    $.each(categories, function(i, str) {
      if (substrRegex.test(str)) {
        matches.push(str);
      }
    });

    cb(matches);
  }


  function edit_dork(dork) {
    if (typeof dork == 'undefined') {
      dork = {}
    }
    var form = $('<form>');
    var ctrl_group = $('<div>', {class: 'form-group row'});
    $.each(['query', 'description', 'category', 'source'], function (i, field) {
      var input_params = {
        class: 'form-control',
        id: field,
        value: dork[field],
        type: 'text'
      };
      if (field == 'category') {
        input_params.class += ' typeahead';
      }
      ctrl_group.append($('<label>', {
          for: field,
          class: "col-sm-2 form-control-label",
          text: uppercase_first(field)
        }))
        .append($('<div>', {class: "col-sm-10"})
          .append($('<input>', input_params))
        )
    });
    ctrl_group.append($('<label>', {
        for: 'search_engine',
        class: "col-sm-2 form-control-label",
        text: 'Search Engine'
      }))
      .append($('<div>', {class: "col-sm-10"})
        .append($('<select>', {
          class: 'form-control',
          id: 'search_engine',
          value: dork.search_engine,
          type: 'select'
        }))
      );
    form.append(ctrl_group);
    form.append($('<button>', {
      type: 'submit',
      text: ((Object.keys(dork).length == 0)? 'Create Dork' : 'Update Dork'),
      class: 'btn btn-primary',
      click: function () {
        save_dork(dork);
        return null;
      }
    }));
    $('#category').typeahead({
        hint: true,
        highlight: true,
        minLength: 1
      },
      { source: categoryMatcher }
    );
    $('#result_modal .modal-body').empty().append(form);
    $('#result_modal .modal-title').text('');
    $('#result_modal').modal('show');
    $.each(search_engines, function(i, se) {
      $('#search_engine').append($('<option>', {
        value: se,
        text: se
      }));
    });
  }

  function save_dork(orig_dork) {
    orig_dork.query = $('#query').val();
    orig_dork.category = $('#category').val();
    orig_dork.description = $('#description').val();
    orig_dork.source = $('#source').val();
    orig_dork.search_engine = $('#search_engine').val();

    if (typeof orig_dork._id != 'undefined') {
      orig_dork._id = orig_dork._id.$oid
    }

    delete orig_dork.date_added;
    delete orig_dork.discovery_date;

    $.post('/update', orig_dork, function (resp) {
      if (resp == 'OK') {
        location.reload();
      } else {
        alert(resp);
      }
    });
  }


  function filter_cat(cat) {
    $.each($('#dorks tr'),
      function(i, val) {
        if (i != 0 && $(val).text().indexOf(cat) == -1) {
          $('#dorks tr').eq(i).hide();
        } else {
          $('#dorks tr').eq(i).show();
        }
      }
    );
  }

  function set_disabled(dbid, status) {
    $.post("/disable", { dbid: dbid, status:status })
      .done(function( data ) {
        if (data != 'OK') {
          alert('Failed to disabled query. Response: ' + data);
          return;
        }
        $("#disabled_"+dbid).removeClass().addClass('label label-'+( (status)? 'danger' : 'success'))
          .text((status) ? 'No' : 'Yes')
          .prop('onclick', "set_disabled('" + dbid + "', " + ( (status) ? "true" : "false" ) + "); return null;")
      });
  }
});