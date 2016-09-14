$(document).ready(function () {

  console.log('[x] Dorky.');

  toastr.options = {positionClass: "toast-bottom-right"};

  $('#result_modal').modal({show: false});
  $('#blacklist_modal').modal({show: false});

  $('#create_new').click(function () { editDork(); });

  $('#show_blacklist').click(function () {
    $.post('/get', {what: 'blacklist'}, function (resp) {
      console.log(resp);
      showBlacklist(resp.blacklist);
    }).fail(function (resp) {
      console.log(resp);
      toastr.error('Unable to fetch blacklist.');
    });
  });

  $('#show_text_blacklist').click(function () {
    $('#url_blacklist').hide();
    $('#text_blacklist').show();
  });

  $('#show_url_blacklist').click(function () {
    $('#text_blacklist').hide();
    $('#url_blacklist').show();
  });

  dorks = [];
  categories = [];

  searchEngines = ['google', 'google_customsearch', 'bing', 'shodan'];

  $.post('/get', {what: 'dorks'}, function (resp) {
    dorks = resp.dorks;
    categories = resp.categories;
    showCategories();
    showDorks();
  });

  function showCategories() {
    $.each(categories, function (i, cat) {
      $('#categories').append($('<td>')
        .append($('<a>', {
          href: '#',
          text: cat,
          click: function () {
            filterCategory(cat);
            return null;
          }
        }))
      )
    });
  }

  function showDorks() {
    var tbl = $('#dorks');
    $.each(dorks, function (i, dork) {
      var tr = $('<tr>', {dbid: dork._id.$oid})
        .append($('<td>')
          .append($('<a>', {
            text: 'Edit',
            role: 'button',
            click: function () {
              editDork(dork);
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
            role: 'button',
            click: function () {
              setDisabled(dork._id.$oid, !dork.disabled);
              return null;
            },
            class: "label label-" + ((dork.disabled)? 'danger' : 'success'),
            text: ((!dork.disabled)? 'Yes' : 'No')
          }))
        )
        .append($('<td>')
          .append($('<a>', {
            role: 'button',
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
          var tbl = $('<table>', {class: 'table table-hover'});
          tbl.append($('<tr><th>Title</th><th>Summary</th><th>Engine ID</th></tr>'))
          $.each(response.results, function (i, row) {
            tbl.append($('<tr>')
              .append($('<td>', {text: row.result.title}))
              .append($('<td>', {text: row.result.description}))
              .append($('<td>', {text: row.engine_id})));
          });
          $('#result_modal .modal-body').empty().append(tbl);
          $('#result_modal .modal-title').text('Results');
          $('#result_modal').modal('show');
        });
        return false;
      });
    });
  }

  function uppercaseFirst (str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  function editDork(dork) {
    if (typeof dork == 'undefined') {
      dork = {}
    }
    var form = $('<form>');
    var ctrlGroup = $('<div>', {class: 'form-group row'});
    $.each(['query', 'description', 'category', 'source'], function (i, field) {
      var inputParams = {
        class: 'form-control',
        id: field,
        value: dork[field],
        type: 'text'
      };
      if (field == 'category') {
        inputParams['data-provide'] = 'typeahead';
        inputParams.autocomplete = 'off';
      }
      ctrlGroup.append($('<label>', {
          for: field,
          class: "col-sm-2 form-control-label",
          text: uppercaseFirst(field)
        }))
        .append($('<div>', {class: "col-sm-10"})
          .append($('<input>', inputParams))
        )
    });
    ctrlGroup.append($('<label>', {
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
    form.append(ctrlGroup);
    form.append($('<button>', {
      type: 'submit',
      text: ((Object.keys(dork).length == 0)? 'Create Dork' : 'Update Dork'),
      class: 'btn btn-primary',
      click: function () {
        saveDork(dork);
        return null;
      }
    }));
    if (Object.keys(dork).length > 0) {
      form.append($('<button>', {
        type: 'submit',
        text: 'Delete Dork And Results',
        class: 'btn btn-danger pull-right',
        click: function () {
          deleteDork(dork);
          return false;
        }
      }));
    }
    $('#result_modal .modal-body').empty().append(form);
    $('#result_modal .modal-title').text('');
    $('#result_modal').modal('show');
    $.each(searchEngines, function(i, se) {
      $('#search_engine').append($('<option>', {
        value: se,
        text: se
      }));
    });
    $('#category').typeahead(
      { source: categories }
    );
  }

  function saveDork(orig_dork) {
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
      location.reload();
    }).fail(function (response) {
      console.log(response);
      toastr.error(response.responseText);
    });
  }

  function unique(array) {
    return $.grep(array, function(el, index) {
      return index === $.inArray(el, array);
    });
  }

  function showBlacklist(blacklist) {
    var textBl = blacklist.text || [],
        urlBl = blacklist.url || [];

    $('#text_blacklist').val(textBl.join('\n'));
    $('#url_blacklist').val(urlBl.join('\n'));

    $('#save_blacklist').unbind('click').click(function () {
      // Decide what changes are being made.
      var textNew = $.map($('#text_blacklist').val().split('\n'), $.trim);
      var urlNew = $.map($('#url_blacklist').val().split('\n'), $.trim);

      var textDiff = blacklistDifference('text', textBl, textNew);
      var urlDiff = blacklistDifference('url', urlBl, urlNew);
      var sumDiff = {
        add: unique(textDiff.add.concat(urlDiff.add)),
        remove: unique(textDiff.remove.concat(urlDiff.remove))
      };
      console.log('[x] Difference:');
      console.log(sumDiff);

      if (Object.keys(sumDiff.add).length == 0 && Object.keys(sumDiff.remove).length == 0) {
        toastr.info('No changes made.');
        $('#blacklist_modal').modal('hide');
        return;
      }

      console.log('[x] Requesting blacklist update.');
      $.post('/edit_blacklist', {updates: JSON.stringify(sumDiff)}, function () {
        toastr.success('Blacklist updated.');
        $('#blacklist_modal').modal('hide');
      }).fail(function (response) {
        console.log(response);
        toastr.error('Editing blacklist failed:' + response.responseText);
      });
    });

    $('#blacklist_modal').modal('show');
  }

  /** Compare an updated blacklist to the old one and return appropriate
   * arguments for the edit_blacklist endpoint.
   */
  function blacklistDifference(type, oldBlacklist, newBlacklist) {
    var args = {remove: [], add: []};
    $.each(newBlacklist, function (i, val) {
      if (val.length > 0 && oldBlacklist.indexOf(val) == -1) {
        args.add.push({term: val, type: type});
      }
    });
    $.each(oldBlacklist, function (i, val) {
      if (val.length > 0 && newBlacklist.indexOf(val) == -1) {
        args.remove.push({term: val, type: type})
      }
    });
    return args;
  }

  function filterCategory(cat) {
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

  function deleteDork(dbid) {
    var resp = confirm('Are you sure you want to delete this dork and all results?');
    console.log(resp);
    if (resp) {
      $.post("/delete", {dbid: dbid._id.$oid}, function () {
        location.reload();
      }).fail(function (response) {
        console.log(response);
        toastr.error('Failed to delete dork. Response: ' + response.responseText);
      });
    } else {
      toastr.info('Not deleting dork.');
    }
  }

  function setDisabled(dbid, status) {
    $.post("/disable", { dbid: dbid, status: status }, function( data ) {
        $("#disabled_"+dbid).removeClass().addClass('label label-'+( (status)? 'danger' : 'success'))
          .text((status) ? 'No' : 'Yes')
          .unbind('click').click(function () {
            setDisabled(dbid, !status);
            return false;
          })
      }).fail(function (response) {
        console.log(response);
        toastr.error('Failed to disable dork. Response: ' + response.responseText);
      });
  }
});