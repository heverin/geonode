Ext.onReady(function() {	
	// set Weave fullscreen
	Ext.get("weave").set({
		height: Ext.get(document.body).getHeight() - Ext.get("header-wrapper").getHeight() - 4,
		width: Ext.get(document.body).getWidth()
	});
});

var initWeave = function(weave) {	
	// load existing or default sessionstate
	var sessionstateUrl = window.location.href + "sessionstate";
	Ext.Ajax.request({
		url: sessionstateUrl,
		method: 'GET',
		success: function(xhr) {
			var sessionstate = Ext.decode(xhr.responseText);
			weave.setSessionState([], sessionstate);
		},
		failure: function(xhr) {
			console.log('Failure!\n' + xhr.responseText);
		}
	});
}

var initMetadataForm = function(weave, options) {
/*
* Handles Visualization metadata (title & description)
* and saving the session state.
*/
	// initial visualization url, used for form-POST
	var visUrl = window.location.href;
	
	// metadata window
	var metadataWin = new Ext.Window({
		title: "About your Visualization",
		width: 340,
		height: 220,
		x: Ext.get(document.body).getWidth()/2 - 170,
		y: 140,
		layout: "fit",
		border: false,
		closable: false,
		items: [{
			xtype: "form",
			id: "metadataForm",
			bodyStyle:"padding:10px",
			defaults: {
				width: 200
			},
			items: [{
				xtype: "textfield",
				id: "title",
				fieldLabel: "Title"
			}, {
				xtype: "textarea",
				id: "abstract",
				height: 100,
				fieldLabel: "Abstract"
			}, {
				xtype: "hidden",
				id: "sessionstate"
			}],
			buttons:[{
				text: "Cancel",
				handler: function() {
					metadataWin.hide();
				}
			}]
		}]
	});
	
	// save visualization
	var saveVisualizationButton = new Ext.Button({
		renderTo: "save_visualization",
		text: "Save Visualization",
		handler: function() {
			// update sessionstate in metadataform
			Ext.getCmp("metadataForm").getForm().setValues({
				"sessionstate": JSON.stringify(weave.getSessionState([]))
			});
			// open metadata window
			metadataWin.show();
		}
	});
	
	// add a "Save as Copy" button to metadata form
	if (options["permissions"]["copy"]) {
		Ext.getCmp("metadataForm").addButton(
			"Save as Copy",
			function() { 
				// hide window
				metadataWin.hide();
				// set POST url to default
				visUrl = "/visualizations/"
				// save form data
				saveVisualization();
			}
		);
	}
	
	// add a "Save" button to metadata form
	if (options["permissions"]["change"]) {
		Ext.getCmp("metadataForm").addButton(
			"Save",
			function() { 
				// hide window
				metadataWin.hide();
				// save form data
				saveVisualization();
			}
		);
	}
	
	// upate existing title and abstract
	Ext.getCmp("metadataForm").getForm().setValues({
		"title": options["title"],
		"abstract": options["abstract"],
		"sessionstate": JSON.stringify(weave.getSessionState([]))
	});
	
	// save session state
	var saveVisualization = function() {
		// get form data
		var metadata = Ext.getCmp("metadataForm").getForm().getValues();
		Ext.Ajax.request({
			url: visUrl,
			method: "POST",
			params: metadata,
			success: function(xhr, params) {
				// url for newly created visualization
				// no responseText (visid) returned if existing visualization is saved
				if (xhr.responseText) visUrl = visUrl + Ext.decode(xhr.responseText).visid + "/";
				// change title
				var vistitle = Ext.DomHelper.overwrite(
					"visualization-title-header",
					{
						tag: "a",
						href: visUrl,
						html: metadata["title"] || "Your Visualization"
					}
				);
				// show user that everything went well
				Ext.get("savemsg").update("...was successfully saved!").fadeIn().pause(2).fadeOut();
			},
			failure: function(xhr, params) {
				Ext.Msg.show({
					title: "Oops, an error occurred...",
					msg: xhr.responseText,
					buttons: Ext.MessageBox.OK,
					icon: Ext.MessageBox.WARNING
				});
			}
		});
	}
	
	// embed button
	var embedVisualizationButton = new Ext.Button({
		renderTo: "embed_code",
		text: "Embed Visualization",
		handler: function() {
			// embed code
			var embedCodeWin = new Ext.Window({
				title: "Copy the code below to embed your Visualization",
				width: 340,
				height: 160,
				x: Ext.get(document.body).getWidth()/2 - 170,
				y: 140,
				layout: "fit",
				border: false,
				closable: true,
				items: [{
					xtype: "form",
					id: "embedCodeForm",
					bodyStyle:"padding:10px",
					hideLabels: true,
					items: [{
						xtype: "textarea",
						id: "embedcode",
						height: 110,
						width: 306,
						value: getEmbedCode(visUrl)
					}]
				}]
			}).show();
		}
	});
}

// little helper to compile the embed string
var getEmbedCode = function(visUrl) {
	embedCode = "<iframe width='500' height='350' frameborder='0' scrolling='no' marginheight='0' marginwidth='0' src='" + visUrl + "embed'></iframe><br /><small><a href='" + visUrl + "'>View Larger Visualization</a></small>";
	return embedCode;
}
